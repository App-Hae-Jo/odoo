from odoo import fields, models, api
from odoo.exceptions import UserError

class ILoadShippingMarkWizard(models.TransientModel):
    _name = 'iload.shipping.mark.wizard'
    _description = '쉬핑 마크 생성 위자드'

    order_detail_id = fields.Many2one(
        'iload.order.detail',
        string='주문 상세',
        required=True,
        ondelete='cascade',
        help="쉬핑 마크를 생성할 주문 상세 정보입니다."
    )

    discharging_port = fields.Char(string='도착지 항구', required=True)
    shipper_name = fields.Char(string='무역업체 명칭', required=True)
    shipper_tel = fields.Char(string='무역업체 연락처', required=True)
    car_name = fields.Char(string='차량명', required=True)
    vin_no = fields.Char(string='차대번호', required=True)
    final_destination = fields.Char(string='최종 도착지 항구 및 국가', required=True)

    template_type = fields.Selection([
        ('template_a', '양식 A'),
        ('template_b', '양식 B'),
    ], string='양식 선택', required=True, default='template_a')

    @api.model
    def default_get(self, fields):
        res = super(ILoadShippingMarkWizard, self).default_get(fields)
        if self._context.get('active_model') == 'iload.order.detail' and self._context.get('active_id'):
            order_detail = self.env['iload.order.detail'].browse(self._context['active_id'])
            res['order_detail_id'] = order_detail.id
            res['car_name'] = order_detail.vehicle_id.name or ''
            res['vin_no'] = order_detail.chassis_number or ''
            # TODO: Add default values for discharging_port, shipper_name, shipper_tel, final_destination
            # These might come from order_detail.order_id or related partner information
        elif self._context.get('active_model') == 'iload.shipping' and self._context.get('active_id'):
            shipping_record = self.env['iload.shipping'].browse(self._context['active_id'])
            res['order_detail_id'] = shipping_record.order_detail_id.id
            res['car_name'] = shipping_record.order_detail_id.vehicle_id.name or ''
            res['vin_no'] = shipping_record.order_detail_id.chassis_number or ''
            # TODO: Add default values for discharging_port, shipper_name, shipper_tel, final_destination
            # These might come from shipping_record.order_detail_id.order_id or related partner information
        return res

    def print_shipping_mark(self):
        self.ensure_one()
        template_id = 'iload_back_office.iload_shipping_mark_template_a' if self.template_type == 'template_a' else 'iload_back_office.iload_shipping_mark_template_b'

        report_content = self.env['ir.ui.view']._render_template(
            template_id,
            {
                'doc': self.order_detail_id,
                'wizard': self,
            }
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'iload.customs.print.wizard', # Reusing customs print wizard for display
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_detail_id': self.order_detail_id.id,
                'default_report_content': report_content,
            },
        }
