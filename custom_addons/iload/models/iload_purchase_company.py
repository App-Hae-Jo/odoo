from odoo import models, fields, _

class IloadPurchaseCompany(models.Model):
    _name = 'iload.purchase.company'
    _description = 'iLoad 거래처(구매)'

    name = fields.Char(string='거래처명', required=True, help="거래처의 이름 또는 상호")
    
    # 1. 사업자 유형 필드
    # 이 필드는 이 거래처가 개인사업자인지, 법인사업자인지, 아니면 사업자가 아닌 순수 개인인지를 구분합니다.
    business_type = fields.Selection([
        ('individual_business', '개인사업자'),
        ('corporate_business', '법인사업자'),
        ('none', '해당 없음'), # 사업자가 아닌 순수 개인
    ], string='사업자 유형', default='none', required=True,
    help="거래처의 사업자 유형을 선택합니다. '해당 없음'은 사업자가 아닌 개인을 의미합니다.")

    # 2. 국적/거주자 유형 필드
    # 이 필드는 거래처의 국적 또는 거주자 구분을 나타냅니다.
    nationality_type = fields.Selection([
        ('domestic', '내국인'),
        ('foreign', '외국인'),
    ], string='국적 유형', default='domestic', required=True,
    help="거래처의 국적/거주자 유형을 선택합니다.")

    # business_type과 nationality_type에 따라 필요할 수 있는 필드들 (예시)
    company_registration_number = fields.Char(
        string='사업자등록번호',
        help="개인사업자 또는 법인사업자의 사업자등록번호입니다.",
        # 'business_type'이 'none'이 아닐 때만 보이도록 설정할 수 있습니다.
        # states={'business_type': [('in', ['individual_business', 'corporate_business'])]}
    )
    resident_registration_number = fields.Char(
        string='주민등록번호',
        help="내국인 개인의 주민등록번호입니다.",
        # 'nationality_type'이 'domestic'이고 'business_type'이 'none'일 때만 보이도록 설정
        # states={'nationality_type': [('not in', ['foreign'])], 'business_type': [('in', ['none'])]}
    )
    foreign_registration_number = fields.Char(
        string='외국인등록번호',
        help="외국인 개인의 외국인등록번호입니다.",
        # 'nationality_type'이 'foreign'일 때만 보이도록 설정
        # states={'nationality_type': [('in', ['foreign'])]}
    )
    
    # 예시: 연락처, 주소 등 일반적인 거래처 정보
    phone = fields.Char(string='전화번호')
    email = fields.Char(string='이메일')
    street = fields.Char(string='주소')
    city = fields.Char(string='도시')
    zip = fields.Char(string='우편번호')
    country_id = fields.Many2one('res.country', string='국가')

    # Many2one 또는 One2many 관계 필드 등 필요에 따라 추가
    # 예를 들어, 해당 거래처와 연결된 구매 차량 기록 등
    # purchase_car_ids = fields.One2many('iload.car', 'purchase_company_id', string="매입 차량")

    # _sql_constraints (필요하다면 유니크 제약 조건 등 추가)
    _sql_constraints = [
        ('name_unique', 'unique(name)', '동일한 이름의 거래처가 이미 존재합니다.'),
    ]