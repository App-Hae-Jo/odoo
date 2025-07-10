# custom_addons/iload/models/ocr_upload_wizard.py

from odoo import models, fields, api, _ # _ (번역), api (데코레이터) 등 필수 모듈 임포트
import base64 # 바이너리 데이터 인코딩/디코딩용
import logging # 로그 출력용
from datetime import date # 오늘 날짜를 가져오기 위해 import
from odoo.exceptions import UserError # 디버깅을 위해 UserError import (선택 사항)
from odoo.tools.safe_eval import safe_eval # <--- 이 부분이 핵심 수정입니다! safe_eval 함수를 직접 임포트
from ..vlm.ocr_factory import VLMProcessor
from ..vlm.convert_image import convert_pdf_to_image

_logger = logging.getLogger(__name__) # 로그를 위한 로거 생성

class IloadOcrUploadVehicleWizard(models.TransientModel):
    _name = 'iload.ocr.upload.vehicle.wizard' # 모델의 기술 이름
    _description = '구매 문서 OCR 업로드 마법사' # Odoo UI에 표시될 설명
    document = fields.Binary(string="문서 파일", required=True) # 파일 업로드 필드
    document_name = fields.Char(string="파일 이름") # 업로드된 파일의 이름
    document_type = fields.Selection([
        ('contract', '매매 계약서'),
        ('registration_cert', '자동차 등록증')
    ], string='문서 유형', required=True, default='contract', help="문서의 분류입니다.")
    
    def _get_vlm_processor(self):
        """VLMProcessor 인스턴스를 반환하는 헬퍼 메서드"""
        return VLMProcessor()
    
    @api.model
    def default_get(self, fields_list):
        # 위자드 팝업이 열릴 때 기본값을 설정하는 메서드 (현재는 특별한 로직 없음)
        res = super().default_get(fields_list)
        return res

    def action_upload_and_process_ocr(self):
        self.ensure_one()

        # HAJINTODO
        if self.document and self.document_name:
            _logger.info(f"문서 업로드 감지: 파일명 '{self.document_name}'")
            try:
                decoded_content = base64.b64decode(self.document).decode('utf-8', errors='ignore')
                inputs = convert_pdf_to_image(decoded_content)
                # _logger.info(f"문서 내용 (디코딩됨, 예시): {decoded_content}")
            except Exception as e:
                _logger.error(f"문서 내용 디코딩 중 오류 발생: {e}")
        else:
            _logger.warning("업로드된 문서 파일이 없거나 파일 이름이 없습니다. (OCR 처리 불가)")

        vlm_processor = self._get_vlm_processor()
        _logger.info(f"{inputs}")
        results = vlm_processor.extract_fields(inputs)
        _logger.info(f"문서 내용 : {results}")

        action = self.env.ref('iload.action_iload_vehicle_acquisition_view').read()[0] 
        
        action.update({
            'type': 'ir.actions.act_window',           
            'res_model': 'iload.vehicle.acquisition',   
            'view_mode': 'form',                        
            'target': 'current',                        
            'res_id': False,                            
            'views': [(self.env.ref('iload.view_iload_vehicle_acquisition_form').id, 'form')],
            'display_name': _('새 차량 매입 (OCR)'), # Odoo UI 상단에 표시될 제목 (Odoo 15+ 적용)
        })

        existing_context = safe_eval(action.get('context', '{}')) if isinstance(action.get('context'), str) else action.get('context', {})
        
        action['context'] = existing_context | {
            f'default_{key}': value
            for key, value in results.items()
        }

        if self.document:
            document_default_value = (
                0, 0, {
                    'name': self.document_name or f'OCR 문서 ({self.document_type})',
                    'attachment': self.document,
                    'document_type': self.document_type,
                    'issue_date': date.today(),
                }
            )
            # One2many 필드에 기본값을 추가할 때는 리스트 형태로 전달
            action['context']['default_acquisition_document_ids'] = [document_default_value]
        
        # 최종 액션 딕셔너리 내용을 서버 로그에 출력
        _logger.info(f"반환될 최종 액션 딕셔너리: {action}")

        return action