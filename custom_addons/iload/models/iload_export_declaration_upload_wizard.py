# -*- coding: utf-8 -*-
import base64
from odoo import fields, models, api
from odoo.exceptions import UserError

class ILoadExportDeclarationUploadWizard(models.TransientModel):
    _name = 'iload.export.declaration.upload.wizard'
    _description = '신고서 업로드 위자드'

    order_detail_id = fields.Many2one(
        'iload.order.detail',
        string='주문 상세',
        required=True,
        ondelete='cascade',
        help="신고서를 업로드할 주문 상세 정보입니다."
    )
    document_name = fields.Char(
        string='문서명',
        required=True,
        help="업로드할 신고서의 이름입니다."
    )
    attachment = fields.Binary(
        string='첨부 파일',
        required=True,
        help="업로드할 신고서 파일입니다."
    )
    issue_date = fields.Date(
        string='발행일',
        help="신고서의 발행일입니다."
    )

    @api.model
    def default_get(self, fields):
        res = super(ILoadExportDeclarationUploadWizard, self).default_get(fields)
        if self._context.get('active_model') == 'iload.order.detail' and self._context.get('active_id'):
            order_detail = self.env['iload.order.detail'].browse(self._context['active_id'])
            if order_detail.state != 'customs_clearance_in_progress':
                raise UserError("신고서는 '통관 진행 중' 상태에서만 업로드할 수 있습니다.")
            res['order_detail_id'] = order_detail.id
            res['document_name'] = f"수출신고필증_{order_detail.chassis_number or ''}"
        return res

    def upload_declaration(self):
        self.ensure_one()
        if not self.attachment:
            raise UserError("업로드할 파일을 선택해 주십시오.")

        # Create an iload.export.document record
        self.env['iload.export.document'].create({
            'name': self.document_name,
            'order_detail_id': self.order_detail_id.id,
            'attachment': self.attachment,
            'document_type': 'export_declaration',
            'issue_date': self.issue_date,
        })

        # Optionally, update the state of the order detail if needed after upload
        # For example, if uploading the declaration moves it to 'shipping_prep'
        if self.order_detail_id.state == 'customs_clearance_in_progress':
            self.order_detail_id.write({'state': 'shipping_prep'})

        return {
            'name': '수출 관련 문서',
            'type': 'ir.actions.act_window',
            'res_model': 'iload.export.document',
            'view_mode': 'tree,form,kanban',
            'domain': [('order_detail_id', '=', self.order_detail_id.id)], # Filter to show only documents for the current order detail
            'context': {'default_order_detail_id': self.order_detail_id.id},
        }