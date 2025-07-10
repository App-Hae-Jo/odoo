from odoo import http
from odoo.http import request
import logging
import base64

from custom_addons.iload_test.services.document_service import DocumentService

_logger = logging.getLogger(__name__)

class ILoadController(http.Controller):

    @http.route('/iload', auth='public', website=True)
    def iload_home(self, **kw):
        return http.request.render('iload.iload_home_template', {})

    @http.route('/iload/ocr', auth='public', website=True)
    def iload_ocr_test_page(self, **kw):
        """ OCR 테스트 및 파일 업로드 페이지를 렌더링합니다. """
        # OCR 업로드 페이지 초기 렌더링
        return request.render('iload.ocr_test_template', {})

    @http.route('/iload/upload', type='http', auth='public', csrf=False, methods=['POST'])
    def upload_file(self, **post):
        _logger.info("파일 업로드 요청을 받았습니다.")
        uploaded_file = post.get('file')
        ocr_type = post.get('ocr_type', 'paddleocr')
        processing_method = post.get('processing_method', 'pattern')
        
        if not uploaded_file:
            _logger.warning("업로드된 파일이 없습니다.")
            return request.render('iload.error_template', {'error_message': '파일이 업로드되지 않았습니다.'})

        
        file = http.request.httprequest.files.get('file')
        if not file:
            return "파일이 업로드되지 않았습니다."
        
        try:
            file_name = uploaded_file.filename
            file_data = base64.b64encode(uploaded_file.read()) # 파일을 읽어 Base64로 인코딩
            content_type = uploaded_file.content_type

            _logger.info(f"업로드된 파일 처리 중: {file_name}, OCR: {ocr_type}, LLM: {processing_method}")

            # document_service 인스턴스 가져오기
            document_service = DocumentService(env=request.env)

            # 문서 처리 및 레코드 ID 가져오기
            record_id = document_service.process_document_from_upload(
                file_data=file_data.decode('utf-8'), # Base64 문자열 전달
                file_name=file_name,
                content_type=content_type,
                ocr_type=ocr_type,
                llm_method=processing_method
            )

            _logger.info(f"문서 처리 성공. 레코드 ID: {record_id}")

            # 결과 페이지로 리다이렉트 (또는 렌더링)
            return request.render('iload.upload_result_template', {
                'record_id': record_id,
                'file_name': file_name,
                'status_message': '파일이 성공적으로 처리되었습니다!'
            })

        except Exception as e:
            _logger.exception("파일 업로드 및 처리 중 오류 발생.")
            raise
            return request.render('iload.error_template', {'error_message': f'파일 처리 중 오류 발생: {e}'})

    
    @http.route('/iload/history', auth='public', website=True)
    def iload_history(self, **kw):
        """ 처리 이력 페이지를 렌더링합니다. """
        _logger.info("문서 처리 이력 가져오는 중.")
        try:
            records = request.env['iload.document_record'].sudo().search([], order='create_date desc')
            return request.render('iload.history_template', {'records': records})
        except Exception as e:
            _logger.exception("이력 가져오는 중 오류 발생.")
            return request.render('iload.error_template', {'error_message': f'이력을 불러오는 중 오류 발생: {e}'})

    @http.route('/iload/history/<int:record_id>', auth='public', website=True)
    def iload_record_detail(self, record_id, **kw):
        """ 특정 문서 레코드의 상세 페이지를 렌더링합니다. """
        _logger.info(f"레코드 ID: {record_id} 상세 정보 가져오는 중.")
        try:
            record = request.env['iload.document_record'].sudo().browse(record_id)
            if not record.exists():
                return request.render('iload.error_template', {'error_message': f'문서 레코드 ID {record_id}를 찾을 수 없습니다.'})
            return request.render('iload.record_detail_template', {'record': record})
        except Exception as e:
            _logger.exception(f"레코드 ID {record_id} 상세 정보 가져오는 중 오류 발생.")
            return request.render('iload.error_template', {'error_message': f'레코드 상세 정보를 불러오는 중 오류 발생: {e}'})

    @http.route('/test_static', auth='public')
    def test_static(self, **kw):
        """
        모듈 내 정적 파일의 경로 확인을 테스트합니다.
        정적 파일 접근 디버깅에 유용합니다.
        """
        import os
        path = os.path.abspath(os.path.join(
            request.addons_module.get_module_path('iload'),
            'static/src/img/iload_logo.svg' # 실제 존재하는 이미지 경로로 변경 필요
        ))
        return f"<h1>예상 정적 파일 경로:</h1><p>{path}</p>"
