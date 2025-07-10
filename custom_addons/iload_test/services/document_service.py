import logging
import base64
from datetime import datetime
from odoo import api, registry, SUPERUSER_ID

from ..ocr.paddleocr_processor import PaddleOCRProcessor
from ..llm.processor_factory import LLMProcessorFactory
from ..utils.validator import DocumentValidator
from ..utils.file_handler import FileHandler

_logger = logging.getLogger(__name__)

class DocumentService:
    """📄 문서 처리 비즈니스 로직 서비스"""
    
    def __init__(self, env=None):
        self.env = env
        self.ocr_processor = PaddleOCRProcessor()
        self.validator = DocumentValidator()
        self.file_handler = FileHandler()
    
    def process_document(self, file_content, filename, processing_options=None):
        """전체 문서 처리 파이프라인"""
        options = processing_options or {}
        
        try:
            # 1. 파일 검증
            validation_result = self._validate_file(file_content, filename)
            if not validation_result['valid']:
                return self._create_error_result(validation_result['error'])
            
            # 2. OCR 텍스트 추출
            extracted_text = self._extract_text(file_content, filename)
            if not extracted_text:
                return self._create_error_result('텍스트를 추출할 수 없습니다')
            
            # 3. 정보 분석
            analysis_result = self._analyze_text(extracted_text, options)
            
            # 4. 결과 검증 및 신뢰도 계산
            validated_result = self._validate_and_score(analysis_result)
            
            # 5. 데이터베이스 저장
            record_id = self._save_to_database({
                'filename': filename,
                'file_content': base64.b64encode(file_content),
                'extracted_text': extracted_text,
                'processing_method': options.get('method', 'pattern'),
                'confidence_score': validated_result['confidence'],
                'vehicle_number': validated_result['data'].get('차량번호'),
                'owner_name': validated_result['data'].get('소유자'),
                'cancellation_reason': validated_result['data'].get('말소사유'),
            })
            
            return {
                'success': True,
                'data': {
                    'record_id': record_id,
                    'extracted_text': extracted_text,
                    'vehicle_info': validated_result['data'],
                    'confidence': validated_result['confidence'],
                    'processing_method': options.get('method', 'pattern')
                }
            }
            
        except Exception as e:
            _logger.error(f"문서 처리 실패: {e}")
            return self._create_error_result(str(e))
    
    def _validate_file(self, file_content, filename):
        """파일 검증"""
        if not self.file_handler.is_supported_format(filename):
            return {'valid': False, 'error': '지원되지 않는 파일 형식'}
        
        if len(file_content) > 10 * 1024 * 1024:  # 10MB
            return {'valid': False, 'error': '파일 크기가 너무 큽니다 (최대 10MB)'}
        
        return {'valid': True}
    
    def _extract_text(self, file_content, filename):
        """OCR 텍스트 추출"""
        try:
            return self.ocr_processor.extract_text(file_content, filename)
        except Exception as e:
            _logger.error(f"OCR 처리 실패: {e}")
            return ""
    
    def _analyze_text(self, text, options):
        """텍스트 분석"""
        method = options.get('method', 'pattern')
        api_key = options.get('api_key')
        
        # LLM 프로세서 생성
        llm_processor = LLMProcessorFactory.create_processor(method, api_key)
        
        return llm_processor.extract_vehicle_info(text)
    
    def _validate_and_score(self, analysis_result):
        """결과 검증 및 신뢰도 계산"""
        confidence = self.validator.calculate_confidence(analysis_result)
        validated_data = self.validator.validate_extracted_data(analysis_result)
        
        return {
            'data': validated_data,
            'confidence': confidence
        }
    
    def _save_to_database(self, data):
        """데이터베이스 저장"""
        if not self.env:
            return None
        
        try:
            record = self.env['iload.document.record'].create(data)
            return record.id
        except Exception as e:
            _logger.error(f"데이터베이스 저장 실패: {e}")
            return None
    
    def _create_error_result(self, error_message):
        """오류 결과 생성"""
        return {
            'success': False,
            'error': error_message,
            'data': None
        }
