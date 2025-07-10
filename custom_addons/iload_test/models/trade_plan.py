from odoo import models, fields, _

class IloadTradePlan(models.Model):
    _name = 'iload.trade.plan'
    _description = '거래 계획 (자동차 수출용)'

    name = fields.Char(string='거래명', required=True)
    vehicle_vin = fields.Char(string='VIN (차대번호)')
    vehicle_model = fields.Char(string='모델명')
    vehicle_year = fields.Char(string='연식')
    vehicle_color = fields.Char(string='색상')
    purchase_date = fields.Date(string='매입일')
    purchase_price = fields.Monetary(string='매입 금액')
    currency_id = fields.Many2one(
        'res.currency', string='통화', required=True,
        default=lambda self: self.env.company.currency_id.id
    )

    seller_name = fields.Char(string='판매자 이름')
    seller_phone = fields.Char(string='판매자 연락처')

    is_generated_from_ocr = fields.Boolean(string='OCR 생성 여부', default=False)

    cert_reg_file = fields.Binary(string='차량등록증')
    cert_reg_filename = fields.Char()

    delivery_cert_file = fields.Binary(string='차량인수증')
    delivery_cert_filename = fields.Char()

    contract_file = fields.Binary(string='매매계약서')
    contract_filename = fields.Char()

    state = fields.Selection([
        ('draft', '초안'),
        ('confirmed', '확정'),
        ('done', '완료'),
    ], string='상태', default='draft')
