# custom_addons/iload/models/ocr_upload_wizard.py

from odoo import models, fields, api, _ # _ (번역), api (데코레이터) 등 필수 모듈 임포트
import base64 # 바이너리 데이터 인코딩/디코딩용
import logging # 로그 출력용
from datetime import date # 오늘 날짜를 가져오기 위해 import
from odoo.exceptions import UserError # 디버깅을 위해 UserError import (선택 사항)
from odoo.tools.safe_eval import safe_eval # <--- 이 부분이 핵심 수정입니다! safe_eval 함수를 직접 임포트

_logger = logging.getLogger(__name__) # 로그를 위한 로거 생성

class IloadOcrUploadVehicleWizard(models.TransientModel):
    _name = 'iload.ocr.upload.vehicle.wizard' # 모델의 기술 이름
    _description = '구매 문서 OCR 업로드 마법사' # Odoo UI에 표시될 설명

    # 위자드 팝업에 표시될 필드들
    document = fields.Binary(string="문서 파일", required=True) # 파일 업로드 필드
    document_name = fields.Char(string="파일 이름") # 업로드된 파일의 이름
    document_type = fields.Selection([
        ('contract', '매매 계약서'),
        ('registration_cert', '자동차 등록증')
    ], string='문서 유형', required=True, default='contract', help="문서의 분류입니다.")

    @api.model
    def default_get(self, fields_list):
        # 위자드 팝업이 열릴 때 기본값을 설정하는 메서드 (현재는 특별한 로직 없음)
        res = super().default_get(fields_list)
        return res

    def action_upload_and_process_ocr(self):
        # OCR 처리 및 매입 등록 폼을 여는 버튼 클릭 시 실행되는 메서드
        self.ensure_one() # 이 메서드가 단일 위자드 레코드에 대해 실행되도록 보장

        # --- 1. 업로드된 파일 로그 출력 (실제 OCR 엔진 연동은 이 부분에 들어갑니다) ---
        # HAJINTODO
        if self.document and self.document_name:
            _logger.info(f"문서 업로드 감지: 파일명 '{self.document_name}'")
            try:
                # 업로드된 바이너리 파일 내용을 디코딩하여 서버 로그에 출력
                # 아주 큰 파일은 로그에 출력하지 않는 것이 좋습니다.
                # 여기서는 테스트 목적으로 전체 내용을 찍도록 했습니다.
                decoded_content = base64.b64decode(self.document).decode('utf-8', errors='ignore')
                _logger.info(f"문서 내용 (디코딩됨, 예시): {decoded_content}")
            except Exception as e:
                _logger.error(f"문서 내용 디코딩 중 오류 발생: {e}")
        else:
            _logger.warning("업로드된 문서 파일이 없거나 파일 이름이 없습니다. (OCR 처리 불가)")

        # --- 2. OCR 더미 데이터 생성 (이 데이터가 매입 등록 폼에 미리 채워질 것입니다) ---
        # 실제 환경에서는 이 부분에 OCR 엔진을 호출하고, 그 결과값을 파싱하여
        # 'iload.vehicle.acquisition' 모델의 필드에 맞게 딕셔너리를 구성해야 합니다.
        dummy_ocr_data = {
            'name': f'OCR 차량매입_{self.document_name or "미정"}', # 파일명을 기반으로 매입 이름 생성
            'acquisition_date': date.today(), # 매입일: 오늘 날짜
            'seller_name': '더미판매자 상사',
            'seller_registration_no': '123-45-67890',
            'seller_address': '서울시 강남구 테헤란로 123 (더미주소)',
            'seller_contact_person': '김철수',
            'seller_phone': '010-1234-5678',
            'car_registration_number': '더미1234',
            'chassis_number': 'DUMMYVIN123456789',
            'vehicle_name': '더미 차량 모델',
            'english_vehicle_name': 'Dummy Vehicle Model',
            'mileage': 50000,
            'vehicle_weight': 1500, # kg
            'engine_displacement': 2000, # cc
            'acquisition_amount': 25000000.00, # 2천5백만원 (Float 또는 Monetary 필드에 맞게)
            'storage_location': '더미 보관 장소',
            'deregistration_status': False, # 초기에는 말소되지 않음
            # 'deregistration_date': False, # deregistration_status가 True일 때만 필요 (예시)
            'acquisition_from_type': 'individual', # 매입 유형 (개인 또는 법인 등)
            # 'acquisition_currency_id': self.env.ref('base.KRW').id, # 통화 (한국 원) - 필요시 주석 해제 및 base 모듈 의존성 추가
        }

        # --- 3. 매입 등록 폼 액션 생성 및 반환 ---
        # 1. 액션 레코드셋의 데이터를 딕셔너리로 가져옵니다.
        action = self.env.ref('iload.action_iload_vehicle_acquisition_view').read()[0] 
        
        # 2. 액션 딕셔너리에 필요한 값들을 먼저 명시적으로 업데이트합니다.
        #    이렇게 하면 context 병합 전에 올바른 view_mode와 views가 설정됩니다.
        action.update({
            'type': 'ir.actions.act_window',            # 이 액션의 타입은 윈도우 액션
            'res_model': 'iload.vehicle.acquisition',   # 대상 모델은 'iload.vehicle.acquisition'
            'view_mode': 'form',                        # 기본 뷰 모드는 'form' (폼 뷰만 열도록 강제)
            'target': 'current',                        # 현재 창에서 열기 (팝업 아님)
            'res_id': False,                            # 특정 기존 레코드가 아닌, 새 레코드를 생성할 것임을 명시
            # Odoo에게 'view_iload_vehicle_acquisition_form' 뷰를 'form' 타입으로 열라고 지시
            'views': [(self.env.ref('iload.view_iload_vehicle_acquisition_form').id, 'form')],
            'display_name': _('새 차량 매입 (OCR)'), # Odoo UI 상단에 표시될 제목 (Odoo 15+ 적용)
        })

        # 3. action['context']가 문자열일 수 있으므로, safe_eval을 사용하여 딕셔너리로 변환합니다.
        #    action.update()가 적용된 후의 context 값을 사용합니다.
        #    safe_eval 함수가 이제 직접 임포트되었으므로 'tools.' 접두사를 제거합니다.
        existing_context = safe_eval(action.get('context', '{}')) if isinstance(action.get('context'), str) else action.get('context', {})
        
        # 4. 딕셔너리 병합
        action['context'] = existing_context | {
            f'default_{key}': value # 'default_필드명': 값 형태로 컨텍스트에 추가
            for key, value in dummy_ocr_data.items()
        }

        # 업로드된 문서를 acquisition_document_ids에 기본값으로 연결
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