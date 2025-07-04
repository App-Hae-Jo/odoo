from abc import ABC, abstractmethod
from typing import Dict, Optional
import logging

_logger = logging.getLogger(__name__)

class BaseLLMProcessor(ABC):
    """🧠 LLM 프로세서 기본 인터페이스"""
    
    @abstractmethod
    def extract_vehicle_info(self, text: str) -> Dict:
        """차량 정보 추출"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """사용 가능 여부 확인"""
        pass
    
    def validate_api_key(self, api_key: str) -> bool:
        """API 키 검증 (기본 구현)"""
        return bool(api_key and api_key.strip())
    
    def get_processor_info(self) -> Dict:
        """프로세서 정보"""
        return {
            'name': self.__class__.__name__,
            'available': self.is_available(),
            'requires_api_key': True
        }