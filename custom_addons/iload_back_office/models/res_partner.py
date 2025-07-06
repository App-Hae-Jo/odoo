# iload/models/res_partner.py (기존 파일 수정)

from odoo import fields, models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_iload_customer = fields.Boolean(
        string='iLoad 주문 고객',
        help="이 파트너가 iLoad 서비스를 통해 운송 주문을 하는 고객사인지 여부"
    )
    iload_customer_code = fields.Char(
        string='iLoad 고객 코드',
        copy=False,
        help="iLoad 시스템에서 사용하는 고객사 고유 코드입니다."
    )
    customs_clearance_no = fields.Char(
        string='통관 번호',
        help="이 고객사의 수출입 통관에 사용되는 고유 번호입니다. (예: 개인통관고유부호)"
    )
    currency_id = fields.Many2one('res.currency', string='통화', required=True, default=lambda self: self.env.company.currency_id.id, help="주문의 통화")
    destination_country_id = fields.Many2one('res.country', string='수출 국가', required=True, help="화물이 최종적으로 도착할 국가")
    _sql_constraints = [
        ('iload_customer_code_uniq', 'unique (iload_customer_code)', 'iLoad 고객 코드는 유일해야 합니다!'),
    ]