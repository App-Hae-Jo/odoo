# -*- coding: utf-8 -*-
import datetime
from odoo import fields, models, api
from odoo.tools import misc
import base64

class ILoadCustomsPrintWizard(models.TransientModel):
    _name = 'iload.customs.print.wizard'
    _description = '통관 요청서 인쇄 위자드'

    order_detail_id = fields.Many2one(
        'iload.order.detail',
        string='주문 상세',
        required=True,
        ondelete='cascade',
        help="인쇄할 통관 요청서의 주문 상세 정보입니다."
    )

    # 이 위자드에 대한 QWeb 뷰를 직접 정의할 것이므로, 여기에 추가 필드는 필요 없을 수 있습니다.
    # 하지만 QWeb 뷰에서 사용할 데이터를 미리 계산하거나 준비하는 로직이 필요할 수 있습니다.

    report_content = fields.Html(
        string="리포트 내용",
        compute="_compute_report_content",
        sanitize_attributes=False, # Allow all HTML attributes
    )

    @api.depends('order_detail_id')
    def _compute_report_content(self):
        for rec in self:
            if rec.order_detail_id:
                # Render the QWeb template using the order_detail_id as 'doc'
                rec.report_content = self.env['ir.ui.view']._render_template(
                    'iload.iload_customs_print_wizard_qweb',
                    {
                        'doc': rec.order_detail_id,
                        'datetime': datetime,
                    }
                )
            else:
                rec.report_content = False

    def print_report(self):
        self.ensure_one()
        # Create an iload.export.document record
        document_name = f"통관요청서_{self.order_detail_id.chassis_number or ''}_{datetime.date.today().strftime('%Y%m%d')}.html"
        self.env['iload.export.document'].create({
            'name': document_name,
            'order_detail_id': self.order_detail_id.id,
            'attachment': base64.b64encode(self.report_content.encode('utf-8')),
            'document_type': 'customs_request',
            'issue_date': datetime.date.today(),
        })

        # Update the state of the order detail if it's not already in customs_clearance_in_progress
        if self.order_detail_id.state != 'customs_clearance_in_progress':
            self.order_detail_id.write({'state': 'customs_clearance_in_progress'})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': '통관 요청서가 수출 문서로 저장되었습니다.',
                'type': 'success',
                'sticky': False,
            }
        }
