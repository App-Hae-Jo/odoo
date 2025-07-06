# iload/models/iload_order_detail.py

from odoo import fields, models, api
from odoo.exceptions import ValidationError

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
    fuel_type = fields.Selection([
        ('G', '가솔린'),
        ('D', '디젤'),
        ('LPG', 'LPG'),
        ('EV', '전기'),
        ('HY', '하이브리드'),
        ('ETC', '기타'),
    ], string='연료 구분', default='ETC', required=True, help="이 차량의 연료 유형입니다.")
    
    vehicle_year = fields.Char(string='차량 연식', help="차량의 제조 연식입니다. (예: 2023)")
    chassis_number = fields.Char(
        string='차대 번호',
        copy=False, # 복사 시 이 필드는 복사되지 않음
        help="차량의 고유 차대 번호(VIN)입니다. 재고 관리와 연결될 수 있습니다."
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
        ('delivered', '인도 완료'), # 고객에게 최종 인도 완료
        ('cancelled', '취소됨'), # 이 상세 라인(차량)만 취소된 경우
    ], string='상태', default='draft', tracking=True, help="이 주문 상세 건의 현재 진행 상태입니다.")

    # --- 기타 정보 ---
    description = fields.Text(string='상세 설명', help="이 주문 상세에 대한 추가 설명입니다.")

    # 새로 추가된 필드: 이 주문 상세와 관련된 매입 문서들
    acquisition_document_ids = fields.One2many(
        'iload.vehicle.acquisition.document', # 연결될 매입 문서 모델
        'order_detail_id', # 'iload.vehicle.acquisition.document' 모델에 정의된 역방향 필드
        string='매입 관련 문서',
        help="이 주문 상세(차량)와 관련된 모든 매입 문서입니다.",
        readonly=True # 이 필드는 직접 추가하는 것이 아니라 관련 문서가 자동으로 여기에 표시됩니다.
    )

    # --- SQL 제약 조건 (옵션) ---
    _sql_constraints = [
        ('chassis_number_uniq', 'unique(chassis_number)', '차대 번호는 유일해야 합니다!'),
        # 동일 주문 내에서 순서 번호는 유일해야 함 (선택 사항)
        ('order_sequence_uniq', 'unique(order_id, sequence)', '하나의 주문 내에서 상세 라인 순서는 유일해야 합니다!'),
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

    # --- 상태 전환 액션 메서드 (UI의 버튼에 연결될 기능) ---
    def action_set_draft(self):
        """상태를 '초안'으로 되돌립니다. (신중하게 사용)"""
        self.ensure_one() # 한 레코드에 대해서만 동작하도록 강제
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
        if self.state in ('vehicle_acquiring'): # 차량 확보 중인 상태에서 말소 준비 가능
            self.write({'state': 'cancellation_prep'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name}) 상태가 '말소 준비'로 변경되었습니다.")
    
    def action_start_cancellation_in_progress(self):
        """상태를 '말소 진행 중'으로 변경합니다."""
        self.ensure_one()
        if self.state in ('cancellation_prep'):
            self.write({'state': 'cancellation_in_progress'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name}) 상태가 '말소 진행 중'으로 변경되었습니다.")

    def action_start_customs_clearance_prep(self):
        """상태를 '통관 준비'로 변경합니다."""
        self.ensure_one()
        if self.state in ('cancellation_in_progress', 'vehicle_acquiring'): # 말소 완료 후 또는 말소 불필요 시
            self.write({'state': 'customs_clearance_prep'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name}) 상태가 '통관 준비'로 변경되었습니다.")

    def action_start_customs_clearance_in_progress(self):
        """상태를 '통관 진행 중'으로 변경합니다."""
        self.ensure_one()
        if self.state == 'customs_clearance_prep':
            self.write({'state': 'customs_clearance_in_progress'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name}) 상태가 '통관 진행 중'으로 변경되었습니다.")

    def action_start_shipping_prep(self):
        """상태를 '선적 준비'로 변경합니다."""
        self.ensure_one()
        if self.state == 'customs_clearance_in_progress':
            self.write({'state': 'shipping_prep'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name}) 상태가 '선적 준비'로 변경되었습니다.")

    def action_start_shipping_in_progress(self):
        """상태를 '선적 진행 중'으로 변경합니다."""
        self.ensure_one()
        if self.state == 'shipping_prep':
            self.write({'state': 'shipping_in_progress'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name}) 상태가 '선적 진행 중'으로 변경되었습니다.")

    def action_complete_delivery(self):
        """상태를 '인도 완료'로 변경합니다."""
        self.ensure_one()
        if self.state == 'shipping_in_progress':
            self.write({'state': 'delivered'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name}) 상태가 '인도 완료'로 변경되었습니다.")

    def action_cancel_detail(self):
        """이 주문 상세 라인만 '취소됨'으로 변경합니다."""
        self.ensure_one()
        if self.state not in ('delivered', 'cancelled'): # 이미 완료/취소된 상태가 아닐 때만 취소 가능
            self.write({'state': 'cancelled'})
            self.order_id.message_post(body=f"상세 라인 ({self.display_name})이 취소되었습니다.", message_type='comment', subtype_xmlid='mail.mt_note')