from odoo import fields, models, api

class ILoadShipping(models.Model):
    _name = 'iload.shipping'
    _description = 'Iload 선적 정보'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='선적 번호',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default='New',
        help="선적 건을 구분하는 고유 번호입니다."
    )

    order_detail_id = fields.Many2one(
        'iload.order.detail',
        string='관련 주문 상세',
        required=True,
        ondelete='cascade',
        index=True,
        help="이 선적 건이 관련된 주문 상세 정보입니다."
    )

    shipping_method = fields.Selection([
        ('container', '컨테이너 선적'),
        ('ro_ro', 'RO-RO (벌크)'),
    ], string='선적 방법', required=True, default='container', help="차량 선적 방법입니다.")

    shipping_date = fields.Date(
        string='선적 일자',
        default=fields.Date.today(),
        help="실제 선적이 이루어진 날짜입니다."
    )

    shipping_document_ids = fields.One2many(
        'iload.shipping.document',
        'shipping_id',
        string='선적 관련 문서',
        help="이 선적 건과 관련된 모든 문서들입니다."
    )

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('iload.shipping.sequence') or 'New'
        return super().create(vals)

    @api.depends('name', 'order_detail_id.display_name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.name} (주문: {rec.order_detail_id.display_name or '미정'})"
