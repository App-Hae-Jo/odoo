from odoo import fields, models, api

class ILoadShippingDocument(models.Model):
    _name = 'iload.shipping.document'
    _description = 'Iload 선적 문서'
    _order = 'shipping_id, document_type, name'

    name = fields.Char(
        string='문서명',
        required=True,
        help="문서의 제목 또는 이름입니다 (예: 인보이스, 패킹리스트)."
    )

    shipping_id = fields.Many2one(
        'iload.shipping',
        string='관련 선적 건',
        required=True,
        ondelete='cascade',
        index=True,
        help="이 문서가 관련된 선적 정보입니다."
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
                values = {'name': doc.name, 'datas': doc.attachment}
                mimetype = self.env['ir.attachment']._compute_mimetype(values)
                doc.mimetype = mimetype
            else:
                doc.mimetype = False

    document_type = fields.Selection([
        # 공통 서류
        ('invoice', '인보이스'),
        ('packing_list', '패킹리스트'),
        ('transfer_slip', '이체증'),
        ('deregistration_cert', '자동차말소사실증명서'),
        ('scrap_acceptance_cert', '폐차인수증명서'),

        # 컨테이너 선적 서류
        ('shoring_list', '쇼링리스트'),
        ('empty_container_photo', '빈컨테이너 사진'),
        ('before_loading_photo_front_back', '적입전 사진 앞&뒤'),
        ('after_loading_photo', '적입 후 사진'),
        ('loading_50_photo', '컨테이너 적입 50% 작업 사진'),
        ('loading_100_open_door_photo', '컨테이너 적입 100% 후 50% 오픈도어 사진'),
        ('loading_complete_closed_door_photo', '컨테이너 작업 완료후 도어닫음 사진'),
        ('cell_photo', '셀 사진'),
        ('deregistration_copy', '말소증 사본'),
        ('tax_invoice', '세금계산서'),

        # RO-RO 선적 서류 (일부 공통과 겹침)
        # ('deregistration_copy', '말소증 사본'), # 공통 또는 컨테이너에 포함
        # ('tax_invoice', '세금계산서'), # 공통 또는 컨테이너에 포함

        ('other', '기타'),
    ], string='문서 유형', required=True, default='invoice', help="문서의 분류입니다.")

    issue_date = fields.Date(string='발행일', help="문서가 발행된 날짜입니다.")
    description = fields.Text(string='추가 설명', help="문서에 대한 상세 내용입니다.")

    # HAJINTODO: OCR 관련 필드 추가 (예: container_number_ocr_result 등)
