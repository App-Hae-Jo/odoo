import re
import logging
from .base_llm import BaseLLMProcessor
from typing import Optional, Dict

_logger = logging.getLogger(__name__)

class PatternMatcher(BaseLLMProcessor):
    """🔍 패턴 매칭 기반 정보 추출 (무료)"""
    
    def __init__(self, api_key: Optional[str] = None):
        # 패턴 매칭은 API 키 불필요
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self):
        """패턴 초기화"""
        return {
            'vehicle_number': [
                r'차량번호[:\s]*([가-힣0-9\s]{5,12})',
                r'등록번호[:\s]*([가-힣0-9\s]{5,12})',
                r'번호[:\s]*([가-힣0-9\s]{5,12})',
                r'(\d{2,3}[가-힣]\d{4})',
                r'([가-힣]{2,4}\d{2,3}[가-힣]\d{4})',
                r'(\d{2,3}\s*[가-힣]\s*\d{4})',
                r'([가-힣]{2,4}\s*\d{2,3}\s*[가-힣]\s*\d{4})'
            ],
            'owner_name': [
                r'소유자[:\s]*([가-힣]{2,4})',
                r'성명[:\s]*([가-힣]{2,4})',
                r'이름[:\s]*([가-힣]{2,4})',
                r'명의자[:\s]*([가-힣]{2,4})',
                r'소유인[:\s]*([가-힣]{2,4})',
                r'신청인[:\s]*([가-힣]{2,4})'
            ],
            'cancellation_reason': [
                r'말소사유[:\s]*([가-힣]{2,6})',
                r'사유[:\s]*([가-힣]{2,6})',
                r'말소[:\s]*([가-힣]{2,6})',
                r'처리사유[:\s]*([가-힣]{2,6})',
                r'(수출|말소|사고폐차|해체|폐기|분실|도난|폐차|수출말소|멸실|훼손|직권말소)'
            ]
        }
    
    def extract_vehicle_info(self, text: str) -> Dict:
        """패턴 매칭을 통한 차량 정보 추출"""
        try:
            result = {
                "차량번호": self._extract_vehicle_number(text),
                "소유자": self._extract_owner_name(text),
                "말소사유": self._extract_cancellation_reason(text)
            }
            
            _logger.info(f"패턴 매칭 결과: {result}")
            return result
            
        except Exception as e:
            _logger.error(f"패턴 매칭 실패: {e}")
            return {"차량번호": None, "소유자": None, "말소사유": None}
    
    def _extract_vehicle_number(self, text: str) -> Optional[str]:
        """차량번호 추출"""
        for pattern in self.patterns['vehicle_number']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # 공백 제거 후 검증
                clean_match = re.sub(r'\s+', '', match)
                if self._validate_vehicle_number(clean_match):
                    return clean_match
        return None
    
    def _extract_owner_name(self, text: str) -> Optional[str]:
        """소유자명 추출"""
        for pattern in self.patterns['owner_name']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if self._validate_korean_name(name):
                    return name
        
        # 패턴에 매치되지 않은 경우 한글 이름 직접 찾기
        korean_names = re.findall(r'[가-힣]{2,4}', text)
        for name in korean_names:
            if self._validate_korean_name(name) and self._is_likely_person_name(name):
                return name
        
        return None
    
    def _extract_cancellation_reason(self, text: str) -> Optional[str]:
        """말소사유 추출"""
        valid_reasons = [
            '수출', '말소', '사고폐차', '해체', '폐기', 
            '분실', '도난', '폐차', '수출말소', '멸실', '훼손', '직권말소'
        ]
        
        # 정확한 매칭 우선
        for reason in valid_reasons:
            if reason in text:
                return reason
        
        # 패턴 매칭
        for pattern in self.patterns['cancellation_reason']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found_reason = match.group(1) if match.groups() else match.group(0)
                if found_reason in valid_reasons:
                    return found_reason
        
        return None
    
    def _validate_vehicle_number(self, vehicle_num: str) -> bool:
        """차량번호 형식 검증"""
        if not vehicle_num or len(vehicle_num) < 5:
            return False
        
        patterns = [
            r'^\d{2,3}[가-힣]\d{4}$',
            r'^[가-힣]{2,4}\d{2,3}[가-힣]\d{4}$'
        ]
        
        return any(re.match(pattern, vehicle_num) for pattern in patterns)
    
    def _validate_korean_name(self, name: str) -> bool:
        """한글 이름 검증"""
        if not name:
            return False
        return bool(re.match(r'^[가-힣]{2,4}$', name))
    
    def _is_likely_person_name(self, name: str) -> bool:
        """사람 이름일 가능성 확인"""
        # 일반적이지 않은 단어들 제외
        excluded_words = {
            '말소', '사유', '번호', '등록', '차량', '소유', '처리', 
            '발급', '기관', '날짜', '일자', '년월', '주소', '전화'
        }
        return name not in excluded_words
    
    def is_available(self) -> bool:
        """항상 사용 가능"""
        return True
    
    def get_processor_info(self) -> Dict:
        """프로세서 정보"""
        return {
            'name': 'Pattern Matcher',
            'available': True,
            'requires_api_key': False,
            'cost': 'free',
            'accuracy': 'medium'
        }