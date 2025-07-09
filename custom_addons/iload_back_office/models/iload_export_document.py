# -*- coding: utf-8 -*-
from odoo import fields, models, api

class ILoadExportDocument(models.Model):
    _name = 'iload.export.document'
    _description = 'Iload 수출 관련 문서'
    _order = 'order_detail_id, document_type, name'

    name = fields.Char(
        string='문서명',
        required=True,
        help="문서의 제목 또는 이름입니다 (예: 수출신고필증, 선하증권)."
    )

    order_detail_id = fields.Many2one(
        'iload.order.detail',
        string='관련 주문 상세',
        required=True,
        ondelete='cascade',
        index=True,
        help="이 문서가 관련된 주문 상세 정보입니다."
    )

    attachment = fields.Binary(
        string='첨부 파일',
        required=True,
        attachment=True,
        help="실제 스캔 문서나 파일을 첨부합니다."
    )

    mimetype = fields.Char(
        string="Mime Type",
        compute="_compute_mimetype",
        store=True,
    )

    @api.depends('attachment', 'name')
    def _compute_mimetype(self):
        for doc in self:
            if doc.attachment:
                values = {'name': doc.name, 'datas': doc.attachment}
                mimetype = self.env['ir.attachment']._compute_mimetype(values)
                doc.mimetype = mimetype
            else:
                doc.mimetype = False

    document_type = fields.Selection([
        ('customs_request', '통관요청서'),
        ('export_declaration', '수출신고필증'),
        ('bl', '선하증권(B/L)'),
        ('other', '기타'),
    ], string='문서 유형', required=True, default='customs_request', help="문서의 분류입니다.")

    issue_date = fields.Date(string='발행일', help="문서가 발행된 날짜입니다.")
    description = fields.Text(string='추가 설명', help="문서에 대한 상세 내용입니다.")

    # --- Override create method for automation ---
    @api.model
    def create(self, vals):
        rec = super(ILoadExportDocument, self).create(vals)
        # If an export declaration is uploaded, update the parent order detail's state
        if rec.document_type == 'export_declaration' and rec.order_detail_id:
            # Assuming the next state is 'shipping_prep'
            rec.order_detail_id.write({'state': 'shipping_prep'})
        return rec
