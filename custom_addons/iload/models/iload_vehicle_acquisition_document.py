# iload/models/iload_vehicle_acquisition_document.py (수정)

from odoo import fields, models, api

class ILoadVehicleAcquisitionDocument(models.Model):
    _name = 'iload.vehicle.acquisition.document'
    _description = 'Iload 차량 매입 문서'
    _order = 'acquisition_id, document_type, name'

    name = fields.Char(
        string='문서명',
        required=True,
        help="문서의 제목 또는 이름입니다 (예: 매매 계약서, 차량 등록증)."
    )

    acquisition_id = fields.Many2one(
        'iload.vehicle.acquisition',
        string='관련 매입 건',
        required=True,
        ondelete='cascade',
        index=True,
        help="이 문서가 관련된 차량 매입 정보입니다."
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
        copy=False,
    )

    @api.depends('attachment', 'name')
    def _compute_mimetype(self):
        for doc in self:
            if doc.attachment:
                # _compute_mimetype은 mimetype 문자열을 직접 반환합니다.
                values = {'name': doc.name, 'datas': doc.attachment}
                mimetype = self.env['ir.attachment']._compute_mimetype(values)
                doc.mimetype = mimetype
            else:
                doc.mimetype = False

    order_detail_id = fields.Many2one(
        'iload.order.detail',
        string='관련 주문 상세',
        help="이 문서가 특정 주문 상세 라인(차량)과 관련된 경우 연결합니다.",
        ondelete='set null'
        # domain은 모델 레벨에서 동적으로 평가될 수 없으므로 제거합니다.
    )
    
    document_type = fields.Selection([
        ('contract', '매매 계약서'),
        ('registration_cert', '자동차 등록증'),
        ('id_card', '신분증 사본'),
        ('bank_statement', '통장 사본'),
        ('invoice', '매입 세금계산서'),
        ('deregistration_application', '말소 신청서'),
        ('deregistration_confirmation', '말소 확인증'),
        ('business_registration_cert', '사업자등록증 사본'),
        ('auto_management_cert', '자동차관리사업 등록증'),
        ('non_fact_confirmation', '비사실용 확인서'),
        ('corporate_seal_cert', '법인 인감증명서 원본'),
        ('corporate_registry_copy', '법인 등기부 등본'),
        ('auto_rental_plan_cert', '자동차대여사업계획 신고 필증'),
        ('other', '기타'),
    ], string='문서 유형', required=True, default='contract', help="문서의 분류입니다.")

    issue_date = fields.Date(string='발행일', help="문서가 발행된 날짜입니다.")
    description = fields.Text(string='추가 설명', help="문서에 대한 상세 내용입니다.")

    acquisition_chassis_number = fields.Char(
        string='매입 차량 차대 번호',
        related='acquisition_id.chassis_number',
        readonly=True,
        store=True,
        help="관련 매입 건의 차대 번호입니다."
    )
    acquisition_seller_name = fields.Char(
        string='매입 판매처 명',
        related='acquisition_id.seller_name',
        readonly=True,
        store=True,
        help="관련 매입 건의 판매처 이름입니다."
    )

    @api.constrains('attachment')
    def _check_attachment_mimetype(self):
        """첨부 파일이 PDF, 이미지 파일 등 적절한 형식인지 확인할 수 있습니다."""
        for rec in self:
            if rec.attachment and rec.mimetype not in ['application/pdf', 'image/jpeg', 'image/png']:
                # raise ValidationError("허용되지 않는 파일 형식입니다. PDF 또는 이미지 파일만 첨부할 수 있습니다.")
                pass

    @api.depends('name', 'document_type', 'acquisition_id.name')
    def _compute_display_name(self):
        for rec in self:
            doc_type_label = dict(rec._fields['document_type']._description_selection(rec.env))[rec.document_type]
            rec.display_name = f"[{doc_type_label}] {rec.name} (매입: {rec.acquisition_id.name or '미정'})"