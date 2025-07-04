from odoo import models, fields, _

class IloadExportRecord(models.Model):
    _name = 'iload.export.record'
    _description = 'iLoad 수출 거래 장부'
    
    voucher_date = fields.Date(string='전표 작성일')
    
    # Many2one 필드 추가: 'iload.purchase.company' 모델과 연결
    # purchase_company_id 라는 기술적 이름을 사용하며, 레이블은 '구매 업체'로 설정합니다.
    purchase_company_id = fields.Many2one(
        'iload.purchase.company', 
        string='구매 업체', 
        required=True, # 구매 업체를 필수로 선택하게 하려면 True로 설정
        help="이 수출 기록과 관련된 구매 업체를 선택합니다."
    )
    
    # 기존 company_name 필드는 삭제하거나 Many2one 필드의 related 필드로 변경하는 것을 고려해보세요.
    # 예: company_name = fields.Char(related='purchase_company_id.name', string='구매 업체명', store=True, readonly=True)
    # 이렇게 하면 purchase_company_id를 선택하면 자동으로 해당 회사의 이름이 채워집니다.
    # 만약 기존 company_name 필드에 다른 의미가 있다면 유지하셔도 됩니다.
    company_name = fields.Char(string='거래 회사 이름') 

    vehicle_name = fields.Char(string='차량명')
    mileage = fields.Integer(string='주행거리 (km)')
    license_plate = fields.Char(string='차량 번호')
    vin = fields.Char(string='차대 번호')
    car_year = fields.Integer(string='연식')
    release_price = fields.Float(string='출고가격(등록증)')
    purchase_price = fields.Float(string='구매금액(면장금액)')
    empty_weight = fields.Float(string='공차중량(kg)')
    length = fields.Float(string='길이')
    height = fields.Float(string='높이 (mm)')
    width = fields.Float(string='너비 (mm)')
    cbm = fields.Float(string='CBM')
    engine_displacement = fields.Integer(string='배기량 (cc)')
    fuel_type = fields.Selection([
        ('gasoline', 'Gasoline'),
        ('diesel', 'Diesel'),
        ('lpg', 'LPG'),
        ('lpi', 'LPI'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('hybrid_gasoline', 'Hybrid (Gasoline + Electric)'),
        ('hybrid_diesel', 'Hybrid (Diesel + Electric)'),
        ('hydrogen_electric', 'Hydrogen + Electric'),
        ('unknown', 'Unknown'),
    ], string='주유 구분')
    seating_capacity = fields.Integer(string='인승')
    modification = fields.Char(string='사양,튜닝 여부')
    export_country = fields.Char(string='수출 예정 또는 완료 국가')

    # Many2one 필드의 예시:
    # fields.Many2one('대상_모델의_이름', string='필드_레이블', [옵션들])
    # 여기서 'iload.purchase.company'는 이전에 정의한 구매업체 모델의 _name입니다.