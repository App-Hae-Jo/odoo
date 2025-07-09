from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import date

class ILoadOrderDetail(models.Model):
    _name = 'iload.order.detail'
    _description = 'Iload 운송 주문 상세 라인'
    _order = 'order_id, sequence' # 상위 주문 ID와 순서에 따라 정렬

    # --- 상위 주문 참조 ---
    order_id = fields.Many2one(
        'iload.order',
        string='주문 참조',
        required=True,
        ondelete='cascade', # 상위 주문(iload.order) 삭제 시 해당 상세 라인도 함께 삭제
        index=True, # 검색 성능 향상을 위해 인덱스 추가
        help="이 상세 라인이 속한 운송 주문입니다."
    )
    sequence = fields.Integer(string='순서', default=10, help="주문 상세 라인의 표시 순서입니다.")

    # --- 차량 및 운송 정보 ---
    vehicle_id = fields.Many2one(
        'iload.vehicle',
        string='차량 모델',
        required=True,
        help="이 주문 상세에 해당하는 차량의 모델입니다."
    )

    # 옵션 2: fuel_type을 독립 필드로 유지하고, 매입 정보와 동기화하지 않음 (기존 로직 유지 시)
    fuel_type = fields.Selection([
        ('G', '가솔린'),
        ('D', '디젤'),
        ('LPG', 'LPG'),
        ('EV', '전기'),
        ('HY', '하이브리드'),
        ('ETC', '기타'),
    ], string='연료 구분', default='ETC', required=True, help="이 차량의 연료 유형입니다.")

    vehicle_year = fields.Char(string='차량 연식', help="차량의 제조 연식입니다. (예: 2023)")
    
    # chassis_number를 related 필드로 변경 (핵심 변경사항)
    chassis_number = fields.Char(
        string='차대 번호',
        related='acquisition_id.chassis_number', # acquisition_id의 chassis_number를 따라감
        store=True, # 검색 가능하도록 DB에 저장
        readonly=True, # 직접 편집 불가능
        help="차량의 고유 차대 번호(VIN)입니다. 관련 차량 매입 정보에서 가져옵니다."
    )

    # 매입 정보 필드
    acquisition_id = fields.Many2one(
        'iload.vehicle.acquisition',
        string='관련 차량 매입 정보',
        # chassis_number와 fuel_type이 related 필드가 되었으므로 domain 조건을 더 단순하게 할 수 있습니다.
        # 예를 들어, 해당 주문 상세에 아직 연결되지 않은 매입 건만 보여주거나,
        # 단순히 'chassis_number' 필드 대신 매입 번호 등으로 매입 정보를 검색하도록 유도할 수 있습니다.
        # 현재는 acquisition_id_uniq 제약 조건이 있어 한 매입 건이 여러 주문 상세에 연결되지 않도록 합니다.
        # domain을 제거하고 사용자가 자유롭게 선택하도록 할 수도 있습니다.
        # domain="[]", 
        help="이 주문 상세에 해당하는 차량이 어떤 매입 건으로 확보되었는지 나타냅니다.",
        ondelete='set null',
        attrs={
            'readonly': [('state', '!=', 'vehicle_acquiring')],
            'required': [('state', '=', 'cancellation_prep')]
        }
    )

    # --- 재무 정보 ---
    amount = fields.Monetary(
        string='주문 금액',
        currency_field='currency_id', # 이 필드의 통화는 currency_id 필드의 값을 따름
        required=True,
        help="이 상세 라인(차량)에 대한 개별 주문 금액입니다."
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='order_id.currency_id', # 상위 주문의 통화와 연동됩니다.
        string='통화',
        readonly=True, # 상위 주문의 통화를 따라가므로 읽기 전용
        store=True, # related 필드이므로 DB에 저장하여 검색 가능하게 함
        help="이 주문 상세 라인의 통화입니다. 상위 주문의 통화와 동일합니다."
    )

    # --- 납기 및 상태 관리 ---
    requested_delivery_date = fields.Date(
        string='납기 요청일',
        required=True,
        help="이 차량에 대한 납품이 요청된 날짜입니다."
    )

    state = fields.Selection([
        ('draft', '초안'), # 초기 생성 상태
        ('vehicle_acquiring', '차량 확보 중'), # 차량 재고를 확인하거나 구매 진행 중
        ('cancellation_prep', '말소 준비'), # 차량 말소를 위한 서류 준비 등
        ('cancellation_in_progress', '말소 진행 중'), # 차량 등록 말소 처리 중
        ('customs_clearance_prep', '통관 준비'), # 통관 서류 준비 중 (면장 발급 준비)
        ('customs_clearance_in_progress', '통관 진행 중'), # 통관 절차 진행 중 (면장 발급 진행 중)
        ('shipping_prep', '선적 준비'), # 선적을 위한 준비 중
        ('shipping_in_progress', '선적 진행 중'), # 실제 선적 중
        ('shipping_fin', '선적 완료'), # 실제 선적 중
        ('delivered', '인도 완료'), # 고객에게 최종 인도 완료
        ('cancelled', '취소됨'), # 이 상세 라인(차량)만 취소된 경우
    ], string='상태', default='draft', tracking=True, help="이 주문 상세 건의 현재 진행 상태입니다.")

    # --- 기타 정보 ---
    description = fields.Text(string='상세 설명', help="이 주문 상세에 대한 추가 설명입니다.")

    # 이 주문 상세와 관련된 매입 문서들 (역방향 One2many)
    acquisition_document_ids = fields.One2many(
        'iload.vehicle.acquisition.document', # 연결될 매입 문서 모델
        'order_detail_id', # 'iload.vehicle.acquisition.document' 모델에 정의된 역방향 필드
        string='매입 관련 문서',
        help="이 주문 상세(차량)와 관련된 모든 매입 문서입니다.",
        readonly=True # 이 필드는 직접 추가하는 것이 아니라 관련 문서가 자동으로 여기에 표시됩니다.
    )

    # 이 주문 상세와 관련된 수출 문서들
    export_document_ids = fields.One2many(
        'iload.export.document',
        'order_detail_id',
        string='수출 관련 문서',
        help="이 주문 상세(차량)와 관련된 모든 수출 문서입니다."
    )

    # --- SQL 제약 조건 (수정) ---
    _sql_constraints = [
        # chassis_number는 related 필드이므로, 여기서는 unique 제약 조건이 불필요하며 제거해야 합니다.
        # ('chassis_number_uniq', 'unique(chassis_number)', '차대 번호는 유일해야 합니다!'),
        ('order_sequence_uniq', 'unique(order_id, sequence)', '하나의 주문 내에서 상세 라인 순서는 유일해야 합니다!'),
        ('acquisition_id_uniq', 'unique(acquisition_id)', '하나의 매입 건은 하나의 주문 상세에만 연결될 수 있습니다!'),
    ]

    # --- Display Name 계산 (목록/관계 필드에 표시될 이름) ---
    @api.depends('vehicle_id.name', 'chassis_number', 'state')
    def _compute_display_name(self):
        """이 주문 상세 레코드의 표시 이름을 계산합니다."""
        for rec in self:
            vehicle_name = rec.vehicle_id.name or '차량 미정'
            chassis = rec.chassis_number or '차대번호 미정'
            state_label = dict(rec._fields['state']._description_selection(rec.env))[rec.state]
            rec.display_name = f"{vehicle_name} ({chassis}) - [{state_label}]"

    # --- Onchange 메서드 (대폭 수정/제거) ---
    # chassis_number가 related 필드이므로 이 onchange는 더 이상 필요 없습니다.
    # @api.onchange('chassis_number')
    # def _onchange_chassis_number_set_acquisition_id(self):
    #     pass # 이 메서드를 제거하는 것을 권장합니다.

    @api.onchange('acquisition_id')
    def _onchange_acquisition_id_set_chassis_number(self):
        """
        '관련 차량 매입 정보' (acquisition_id)가 선택되거나 변경될 때,
        chassis_number는 related 필드로 자동 채워지므로, 여기서는 상태 전환 로직만 유지합니다.
        """
        if self.acquisition_id:
            # self.chassis_number = self.acquisition_id.chassis_number # Related 필드이므로 이 줄은 불필요
            
            # 상태 전환 로직 유지
            if self.state == 'vehicle_acquiring': # '차량 확보 중' 상태에서만 자동 전환
                if self.acquisition_id.deregistration_status:
                    self.state = 'customs_clearance_prep' # 이미 말소되었다면 바로 '통관 준비'
                else:
                    self.state = 'cancellation_prep' # 말소되지 않았다면 '말소 준비'
        elif not self.acquisition_id:
            # acquisition_id가 해제될 경우 chassis_number는 related 필드로 인해 자동으로 비워집니다.
            pass # 추가적인 로직은 불필요

    @api.model
    def create(self, vals):
        record = super(ILoadOrderDetail, self).create(vals)
        if record.acquisition_id:
            # acquisition_id와 order_detail_id 간의 연결만 담당합니다.
            record.acquisition_id.write({'order_detail_id': record.id})
        return record

    def write(self, vals):
        old_acquisition_id = {rec.id: rec.acquisition_id.id for rec in self} if 'acquisition_id' in vals else {}

        res = super(ILoadOrderDetail, self).write(vals)

        for record in self:
            # acquisition_id 필드 변경 감지 및 양방향 링크 관리
            if 'acquisition_id' in vals and record.acquisition_id.id != old_acquisition_id.get(record.id):
                # 이전 매입 건이 있었다면 연결 해제
                if old_acquisition_id.get(record.id):
                    self.env['iload.vehicle.acquisition'].browse(old_acquisition_id[record.id]).write({'order_detail_id': False})
                # 새로운 매입 건이 있다면 연결
                if record.acquisition_id:
                    record.acquisition_id.write({'order_detail_id': record.id})
            # acquisition_id가 False로 설정된 경우 (연결 해제)
            elif 'acquisition_id' in vals and not record.acquisition_id and old_acquisition_id.get(record.id):
                self.env['iload.vehicle.acquisition'].browse(old_acquisition_id[record.id]).write({'order_detail_id': False})

            # --- 필드 동기화 로직 (이제 chassis_number는 related이므로 여기서는 제거) ---
            # 만약 fuel_type이 related가 아니고, order_detail에서 변경 시 acquisition에 반영하고 싶다면 아래 로직 유지
            # if record.acquisition_id: 
            #     update_acquisition_vals = {}
            #     if 'fuel_type' in vals and record.fuel_type != record.acquisition_id.fuel_type:
            #         update_acquisition_vals['fuel_type'] = record.fuel_type
            #     if update_acquisition_vals:
            #         record.acquisition_id.write(update_acquisition_vals)
            # --- 필드 동기화 로직 끝 ---

        return res


    # --- 상태 전환 액션 메서드 (UI의 버튼에 연결될 기능) ---
    def action_set_draft(self):
        """상태를 '초안'으로 되돌립니다. (신중하게 사용)"""
        self.ensure_one()
        self.write({'state': 'draft'})
        self.order_id.message_post(body=f"상세 라인 ({self.display_name}) 상태가 '초안'으로 변경되었습니다.")

    def action_start_acquiring(self):
        """상태를 '차량 확보 중'으로 변경합니다."""
        self.ensure_one()
        if self.state in ('draft', 'cancelled'): # 초안 또는 취소 상태에서 시작 가능
            self.write({'state': 'vehicle_acquiring'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name}) 상태가 '차량 확보 중'으로 변경되었습니다.")

    def action_start_cancellation_prep(self):
        """상태를 '말소 준비'로 변경합니다."""
        self.ensure_one()
        if self.state == 'vehicle_acquiring' and self.acquisition_id:
            self.write({'state': 'cancellation_prep'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name}) 상태가 '말소 준비'로 변경되었습니다.")
        elif self.state == 'vehicle_acquiring' and not self.acquisition_id:
            raise ValidationError("말소 준비 상태로 변경하려면 먼저 '관련 차량 매입 정보'(acquisition_id)를 연결해야 합니다.")
        else:
            raise ValidationError("현재 상태에서는 '말소 준비'로 변경할 수 없습니다.")

    def action_start_cancellation_in_progress(self):
        """상태를 '말소 진행 중'으로 변경합니다."""
        self.ensure_one()
        if self.state == 'cancellation_prep':
            self.write({'state': 'cancellation_in_progress'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name}) 상태가 '말소 진행 중'으로 변경되었습니다.")

    def action_start_customs_clearance_prep(self):
        """상태를 '통관 준비'로 변경합니다."""
        self.ensure_one()
        # '말소 진행 중' 상태에서 통관 준비 가능. 또는 차량 확보 상태에서 바로 통관으로 넘어온 경우도 허용.
        if self.state in ('cancellation_in_progress', 'vehicle_acquiring'):
            self.write({'state': 'customs_clearance_prep'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name}) 상태가 '통관 준비'로 변경되었습니다.")
        else:
            raise ValidationError("현재 상태에서는 '통관 준비'로 변경할 수 없습니다.")

    def action_start_customs_clearance(self):
        """상태를 '통관 진행 중'으로 변경하고 통관 요청서 인쇄 위자드를 엽니다."""
        self.ensure_one()
        if self.state == 'customs_clearance_prep':
            self.write({'state': 'customs_clearance_in_progress'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name}) 상태가 '통관 진행 중'으로 변경되었습니다.")
            return {
                'name': '통관 요청서 인쇄',
                'type': 'ir.actions.act_window',
                'res_model': 'iload.customs.print.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_order_detail_id': self.id},
            }
        else:
            raise ValidationError("현재 상태에서는 '통관 진행'으로 변경할 수 없습니다.")

    def action_start_shipping_prep(self):
        """상태를 '선적 준비'로 변경합니다."""
        self.ensure_one()
        if self.state == 'customs_clearance_in_progress':
            self.write({'state': 'shipping_prep'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name}) 상태가 '선적 준비'로 변경되었습니다.")
        else:
            raise ValidationError("현재 상태에서는 '선적 준비'로 변경할 수 없습니다.")

    def action_start_shipping_in_progress(self):
        """상태를 '선적 진행 중'으로 변경합니다."""
        self.ensure_one()
        if self.state == 'shipping_prep':
            self.write({'state': 'shipping_in_progress'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name}) 상태가 '선적 진행 중'으로 변경되었습니다.")
        else:
            raise ValidationError("현재 상태에서는 '선적 진행 중'으로 변경할 수 없습니다.")

    def action_complete_delivery(self):
        """상태를 '인도 완료'로 변경합니다."""
        self.ensure_one()
        if self.state == 'shipping_in_progress':
            self.write({'state': 'delivered'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name}) 상태가 '인도 완료'로 변경되었습니다.")
        else:
            raise ValidationError("현재 상태에서는 '인도 완료'로 변경할 수 없습니다.")

    def action_cancel_detail(self):
        """이 주문 상세 라인만 '취소됨'으로 변경합니다."""
        self.ensure_one()
        if self.state not in ('delivered', 'cancelled'): # 이미 완료/취소된 상태가 아닐 때만 취소 가능
            self.write({'state': 'cancelled'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name})이 취소되었습니다.", message_type='comment', subtype_xmlid='mail.mt_note')
        else:
            raise ValidationError("이미 완료되거나 취소된 주문 상세는 취소할 수 없습니다.")

    def action_open_export_declaration_wizard(self):
        """
        '신고서 업로드' 위자드를 엽니다.
        선택된 레코드가 하나이고, 상태가 '통관 진행 중'일 때만 허용합니다.
        """
        self.ensure_one() # 단일 레코드만 선택되었는지 확인

        if self.state != 'customs_clearance_in_progress':
            raise ValidationError("신고서 업로드는 '통관 진행 중' 상태에서만 가능합니다.")

        return {
            'name': '신고서 업로드',
            'type': 'ir.actions.act_window',
            'res_model': 'iload.export.declaration.upload.wizard', # 위자드 모델 이름
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_detail_id': self.id},
        }