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

    def action_open_shipping_mark_wizard(self):
        """
        '쉬핑 마크 생성' 위자드를 엽니다.
        선택된 레코드가 하나이고, 연결된 주문 상세의 상태가 '선적 준비' 또는 '선적 진행 중'일 때만 허용합니다.
        """
        self.ensure_one() # 단일 레코드만 선택되었는지 확인

        if not self.order_detail_id:
            raise UserError("관련 주문 상세 정보가 없는 선적 건은 쉬핑 마크를 생성할 수 없습니다.")

        if self.order_detail_id.state not in ('shipping_prep', 'shipping_in_progress'):
            raise UserError("쉬핑 마크는 '선적 준비' 또는 '선적 진행 중' 상태에서만 생성할 수 있습니다.")

        return {
            'name': '쉬핑 마크 생성',
            'type': 'ir.actions.act_window',
            'res_model': 'iload.shipping.mark.wizard', # 위자드 모델 이름
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_shipping_id': self.id, 'active_id': self.id, 'active_model': 'iload.shipping'},
        }
