from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError
from datetime import date

class ILoadVehicleAcquisition(models.Model):
    _name = 'iload.vehicle.acquisition'
    _description = 'Iload 차량 매입 정보'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='매입 번호',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('iload.vehicle.acquisition.sequence') or 'New',
        help="차량 매입 건을 구분하는 고유 번호입니다."
    )

    acquisition_date = fields.Date(
        string='매입 일자',
        required=True,
        default=fields.Date.today(),
        help="차량을 매입한 날짜입니다."
    )
    
    # 매입처 정보 (res.partner 사용하지 않음)
    acquisition_from_type = fields.Selection([
        ('corporate', '법인'),
        ('sole_proprietor', '개인사업자'),
        ('individual', '개인'),
    ], string='매입처 유형', required=True, default='corporate', help="차량을 매입한 주체의 유형입니다.")

    # 판매처 정보 (직접 입력 필드)
    seller_name = fields.Char(
        string='판매처 명',
        required=True,
        help="차량을 판매한 법인, 개인사업자 또는 개인의 이름/상호명입니다."
    )
    seller_registration_no = fields.Char(
        string='판매처 사업자/주민등록번호',
        help="판매처의 사업자등록번호 또는 개인의 주민등록번호/식별번호입니다.",
    )
    seller_address = fields.Char(string='판매처 주소', help="차량 판매처의 주소입니다.")
    seller_contact_person = fields.Char(string='판매처 담당자', help="판매처의 연락 담당자 이름입니다.")
    seller_phone = fields.Char(string='판매처 연락처', help="판매처의 전화번호입니다.")


    # 차량 정보 (실제 매입된 차량의 상세 스펙)
    car_registration_number = fields.Char(string='자동차등록번호', required=True, help="차량의 등록증 상의 고유 등록 번호입니다.")
    chassis_number = fields.Char(
        string='차대 번호',
        required=True,
        copy=False,
        index=True,
        help="차량의 고유 차대 번호(VIN)입니다. 주문 상세(iload.order.detail)와 매칭될 수 있습니다."
    )
    vehicle_id = fields.Many2one(
        'iload.vehicle',
        string='차량 모델 (시스템)',
        help="시스템에 등록된 차량 모델과 매칭합니다. 일관된 데이터 관리에 유용합니다."
    )
    english_vehicle_name = fields.Char(string='영문 차량명', help="차량의 영문 모델명입니다.")
    
    mileage = fields.Float(string='주행거리 (km)', help="매입 당시 차량의 주행거리입니다.")
    vehicle_weight = fields.Float(string='차량 무게 (kg)', help="매입 당시 차량의 중량입니다.")
    engine_displacement = fields.Float(string='배기량 (cc)', help="차량의 엔진 배기량입니다.")

    # 재무 정보
    acquisition_amount = fields.Monetary(
        string='매입액',
        currency_field='acquisition_currency_id',
        required=True,
        help="차량을 매입한 금액입니다."
    )
    acquisition_currency_id = fields.Many2one(
        'res.currency',
        string='매입 통화',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
        help="매입액에 사용된 통화입니다."
    )

    # 보관 및 말소 정보
    storage_location = fields.Char(string='보관 위치', help="매입된 차량이 현재 보관된 물리적 위치입니다.")
    
    deregistration_status = fields.Boolean(string='말소 여부', default=False, help="차량 등록이 말소되었는지 여부입니다.")
    deregistration_date = fields.Date(
        string='말소 일자',
        help="차량이 공식적으로 말소된 날짜입니다.",
        attrs={'invisible': [('deregistration_status', '=', False)]}
    )

    # 이 매입 건이 어떤 주문 상세와 연결되는지
    order_detail_id = fields.Many2one(
        'iload.order.detail',
        string='관련 주문 상세',
        domain="[('chassis_number', '=', chassis_number)]",
        help="이 매입 차량이 특정 주문 상세 라인(차량)을 충족하는 경우 연결됩니다.",
        ondelete='set null'
    )
    # 새로 추가된 필드: 이 매입 건과 관련된 문서들
    acquisition_document_ids = fields.One2many(
        'iload.vehicle.acquisition.document', # 연결될 매입 문서 모델의 _name
        'acquisition_id',                     # 'iload.vehicle.acquisition.document' 모델에 정의된 역방향 Many2one 필드 이름
        string='매입 관련 문서',
        help="이 차량 매입 건과 관련된 모든 문서들입니다."
    )

    _sql_constraints = [
        ('car_registration_number_uniq', 'unique (car_registration_number)', '자동차등록번호는 유일해야 합니다!'),
        ('chassis_number_uniq', 'unique (chassis_number)', '차대 번호는 유일해야 합니다!'),
    ]

    @api.depends('name', 'car_registration_number', 'chassis_number')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.name} ({rec.car_registration_number or '미등록'} / {rec.chassis_number or '미정'})"

    def action_open_deregistration_wizard(self):
        if len(self) > 1:
            raise UserError("말소 등록은 단일 차량에 대해서만 가능합니다.")

        self.ensure_one() # 이제 단일 레코드임을 확신할 수 있으므로 안전하게 사용

        if self.deregistration_status:
            raise UserError("선택된 차량은 이미 말소 처리되었습니다.")

        # 마법사 액션 반환
        return {
            'name': "차량 말소 등록",
            'type': 'ir.actions.act_window',
            'res_model': 'iload.vehicle.deregistration.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_acquisition_id': self.id, 'active_ids': self.ids},
        }
