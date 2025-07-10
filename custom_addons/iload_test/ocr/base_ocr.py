from abc import ABC, abstractmethod
from typing import Optional

class BaseOCRProcessor(ABC):
    """🔍 OCR 프로세서 기본 클래스"""
    
    @abstractmethod
    def extract_text(self, file_content: bytes, filename: str) -> str:
        """파일에서 텍스트 추출"""
        pass
    
    @abstractmethod
    def is_supported_format(self, filename: str) -> bool:
        """지원되는 파일 형식인지 확인"""
        pass
    
    @abstractmethod
    def preprocess_image(self, image_data: bytes) -> bytes:
        """이미지 전처리"""
        pass

