# custom_addons/iload/models/ocr_upload_wizard.py

from odoo import models, fields, api, _ # _ (번역), api (데코레이터) 등 필수 모듈 임포트
import base64 # 바이너리 데이터 인코딩/디코딩용
import logging # 로그 출력용
from datetime import datetime
import re

from datetime import date # 오늘 날짜를 가져오기 위해 import
from odoo.exceptions import UserError # 디버깅을 위해 UserError import (선택 사항)
from odoo.tools.safe_eval import safe_eval # <--- 이 부분이 핵심 수정입니다! safe_eval 함수를 직접 임포트
from ..vlm.ocr_factory import VLMProcessor
from ..vlm.convert_image import convert_pdf_to_image

_logger = logging.getLogger(__name__) # 로그를 위한 로거 생성

def format_korean_date_to_ymd(korean_date_str):
    """
    'YYYY년 MM월 DD일' 또는 'YYYY년 MM월 ' 형식을 'YYYY-MM-DD'로 변환합니다.
    일(DD)이 없는 경우 '01'로 기본값을 설정합니다.
    """
    if not korean_date_str:
        return False # Odoo Date/Datetime 필드는 False를 None으로 처리합니다.

    # 문자열 앞뒤 공백 제거
    korean_date_str = korean_date_str.strip()

    # 'YYYY년 MM월 DD일' 형식 매칭
    match_full = re.match(r'(\d{4})년 (\d{1,2})월 (\d{1,2})일', korean_date_str)
    if match_full:
        year, month, day = match_full.groups()
        try:
            # 유효한 날짜인지 확인
            datetime(int(year), int(month), int(day)).date()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        except ValueError:
            _logger.warning(f"유효하지 않은 날짜 값 (YYYY년 MM월 DD일): '{korean_date_str}'")
            return False

    # 'YYYY년 MM월 ' 형식 매칭 (일이 없는 경우)
    match_month = re.match(r'(\d{4})년 (\d{1,2})월\s*', korean_date_str)
    if match_month:
        year, month = match_month.groups()
        try:
            # 일이 없는 경우 기본값 '01' 설정 및 유효한 날짜인지 확인
            datetime(int(year), int(month), 1).date()
            return f"{year}-{int(month):02d}-01"
        except ValueError:
            _logger.warning(f"유효하지 않은 날짜 값 (YYYY년 MM월): '{korean_date_str}'")
            return False
            
    # 이미 'YYYY-MM-DD' 형식인 경우 (혹은 다른 표준 형식)
    try:
        datetime.strptime(korean_date_str, '%Y-%m-%d').date()
        return korean_date_str
    except ValueError:
        pass # 이 형식도 아니면 다음으로 넘어감
    
    _logger.warning(f"알 수 없는 날짜 형식 '{korean_date_str}'이 감지되었습니다. 변환 불가.")
    return False # 유효하지 않거나 변환 불가능한 경우 False 반환


def clean_numeric_string(numeric_str):
    _logger.debug(f"clean_numeric_string 호출: 입력값 타입={type(numeric_str)}, 값='{numeric_str}'")

    if numeric_str is None:
        _logger.debug("clean_numeric_string: 입력값이 None입니다. 0.0 반환.")
        return 0.0

    s = str(numeric_str).strip() # 문자열로 변환하고 앞뒤 공백 제거
    _logger.debug(f"clean_numeric_string: 1. str().strip() 후: '{s}' (len={len(s)})")

    # 모든 유니코드 공백 문자를 일반 공백으로 변환하고 여러 공백을 하나로 줄인 후 다시 strip
    # (이는 모든 종류의 공백 문자를 처리하는 가장 강력한 방법 중 하나입니다)
    s = ' '.join(s.split()).strip()
    _logger.debug(f"clean_numeric_string: 2. 유니코드/다중 공백 처리 후: '{s}' (len={len(s)})")

    # 쉼표 제거
    s = s.replace(',', '')
    _logger.debug(f"clean_numeric_string: 3. 쉼표 제거 후: '{s}' (len={len(s)})")
    
    # 일반적인 단위 제거 (프롬프트에 추가했더라도 혹시 몰라 코드에서도 처리)
    s = s.replace('원', '').replace('mm', '').replace('cc', '').replace('km', '').strip()
    _logger.debug(f"clean_numeric_string: 4. 단위 제거 및 최종 strip 후: '{s}' (len={len(s)})")

    # 숫자 패턴만 정확히 매칭 (음수, 정수, 소수점 포함)
    match = re.match(r'^(-?\d+(?:\.\d+)?)', s) 
    
    if match:
        numeric_part = match.group(1) # 그룹 1에 해당하는 숫자 부분만 가져옴
        _logger.debug(f"clean_numeric_string: 5. 정규식 매칭 성공, 추출된 숫자 부분: '{numeric_part}'")
        try:
            float_value = float(numeric_part)
            _logger.debug(f"clean_numeric_string: 6. float 변환 성공: {float_value}")
            return float_value
        except ValueError as e:
            _logger.error(f"clean_numeric_string: 7. 최종 float 변환 실패 (ValueError: {e}). 원본: '{numeric_str}', 처리된 최종 문자열: '{s}', 추출된 숫자 부분: '{numeric_part}'")
            return 0.0
    else:
        _logger.warning(f"clean_numeric_string: 8. 숫자 패턴 매칭 실패. 원본: '{numeric_str}', 처리된 최종 문자열: '{s}'")
        return 0.0

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
            try:
                decoded_content = base64.b64decode(self.document)                
                inputs = convert_pdf_to_image(decoded_content)
                # _logger.info(f"문서 내용 (디코딩됨, 예시): {decoded_content}")
            except Exception as e:
                _logger.error(f"문서 내용 디코딩 중 오류 발생: {e}")
        else:
            _logger.warning("업로드된 문서 파일이 없거나 파일 이름이 없습니다. (OCR 처리 불가)")

        vlm_processor = self._get_vlm_processor()
        extract_feature = vlm_processor.extract_fields(inputs)
        
        results = {} 
        if isinstance(extract_feature, dict):
            extracted_feature = extract_feature
            # VLM이 빈 문자열이나 null을 반환할 수 있으므로, Odoo에 빈 문자열로 저장
            string_fields = [
                "name", "acquisition_from_type", "seller_name",
                "seller_registration_no", "seller_address", "seller_contact_person",
                "seller_phone", "car_registration_number", "chassis_number",
                "english_vehicle_name", "acquisition_currency_id", "storage_location",
                "deregistration_status", "fuel_type"
            ]
            for field in string_fields:
                results[field] = str(extracted_feature.get(field, '') or '').strip()
                if results[field].lower() == 'null': # VLM이 'null' 문자열을 반환할 경우 처리
                    results[field] = ''

            # --- 날짜 필드 ---
            # 'acquisition_date'
            if 'acquisition_date' in extracted_feature:
                original_date = extracted_feature['acquisition_date']
                formatted_date = format_korean_date_to_ymd(original_date)
                results['acquisition_date'] = formatted_date
                _logger.info(f"날짜 변환: acquisition_date '{original_date}' -> '{formatted_date}'")
            else:
                results['acquisition_date'] = False # 필드가 아예 없으면 False

            # 'deregistration_date'
            if 'deregistration_date' in extracted_feature:
                original_date = extracted_feature['deregistration_date']
                formatted_date = format_korean_date_to_ymd(original_date)
                results['deregistration_date'] = formatted_date
                _logger.info(f"날짜 변환: deregistration_date '{original_date}' -> '{formatted_date}'")
            else:
                results['deregistration_date'] = False # 필드가 아예 없으면 False

            # --- 숫자 (Float) 필드 ---
            # 'acquisition_amount'
            _logger.info(f"extracted_dataextracted_data{extracted_feature}")
            if 'acquisition_amount' in extracted_feature:
                original_amount_str = extracted_feature['acquisition_amount']
                cleaned_amount = clean_numeric_string(original_amount_str)
                results['acquisition_amount'] = cleaned_amount
                _logger.info(f"금액 변환: acquisition_amount '{original_amount_str}' -> '{cleaned_amount}'")
            else:
                results['acquisition_amount'] = 0.0 # 필드가 없으면 0.0 (혹은 None)

            # 'mileage'
            if 'mileage' in extracted_feature:
                original_mileage_str = extracted_feature['mileage']
                cleaned_mileage = clean_numeric_string(original_mileage_str)
                results['mileage'] = cleaned_mileage
                _logger.info(f"마일리지 변환: mileage '{original_mileage_str}' -> '{cleaned_mileage}'")
            else:
                results['mileage'] = 0.0

            # 'vehicle_weight'
            if 'vehicle_weight' in extracted_feature:
                original_weight_str = extracted_feature['vehicle_weight']
                cleaned_weight = clean_numeric_string(original_weight_str)
                results['vehicle_weight'] = cleaned_weight
                _logger.info(f"차량 중량 변환: vehicle_weight '{original_weight_str}' -> '{cleaned_weight}'")
            else:
                results['vehicle_weight'] = 0.0

            # 'engine_displacement'
            if 'engine_displacement' in extracted_feature:
                original_engine_str = extracted_feature['engine_displacement']
                cleaned_engine = clean_numeric_string(original_engine_str)
                results['engine_displacement'] = cleaned_engine
                _logger.info(f"배기량 변환: engine_displacement '{original_engine_str}' -> '{cleaned_engine}'")
            else:
                results['engine_displacement'] = 0.0
        
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