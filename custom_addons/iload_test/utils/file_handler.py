
import os
import tempfile
import hashlib
from pathlib import Path
import logging

_logger = logging.getLogger(__name__)

class FileHandler:
    """📁 파일 처리 유틸리티"""
    
    def __init__(self):
        self.supported_formats = {'.pdf', '.jpg', '.jpeg', '.png'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_mime_types = {
            'application/pdf',
            'image/jpeg', 
            'image/jpg',
            'image/png'
        }
    
    def is_supported_format(self, filename):
        """지원되는 파일 형식인지 확인"""
        if not filename:
            return False
        return Path(filename).suffix.lower() in self.supported_formats
    
    def validate_file_size(self, file_content):
        """파일 크기 검증"""
        if isinstance(file_content, bytes):
            return len(file_content) <= self.max_file_size
        return False
    
    def get_file_extension(self, filename):
        """파일 확장자 추출"""
        return Path(filename).suffix.lower() if filename else ''
    
    def calculate_file_hash(self, file_content):
        """파일 해시 계산"""
        try:
            return hashlib.md5(file_content).hexdigest()
        except Exception as e:
            _logger.error(f"파일 해시 계산 실패: {e}")
            return None
    
    def create_temp_file(self, file_content, suffix=''):
        """임시 파일 생성"""
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.write(file_content)
            temp_file.flush()
            temp_file.close()
            return temp_file.name
        except Exception as e:
            _logger.error(f"임시 파일 생성 실패: {e}")
            return None
    
    def cleanup_temp_file(self, file_path):
        """임시 파일 삭제"""
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
                return True
        except Exception as e:
            _logger.error(f"임시 파일 삭제 실패: {e}")
        return False
    
    def get_file_info(self, file_content, filename):
        """파일 정보 조회"""
        return {
            'filename': filename,
            'size': len(file_content) if isinstance(file_content, bytes) else 0,
            'extension': self.get_file_extension(filename),
            'hash': self.calculate_file_hash(file_content) if isinstance(file_content, bytes) else None,
            'is_supported': self.is_supported_format(filename),
            'size_valid': self.validate_file_size(file_content)
        }
    
    def validate_file(self, file_content, filename):
        """종합 파일 검증"""
        errors = []
        
        if not filename:
            errors.append("파일명이 없습니다")
        
        if not self.is_supported_format(filename):
            errors.append(f"지원되지 않는 파일 형식입니다. 지원 형식: {', '.join(self.supported_formats)}")
        
        if not isinstance(file_content, bytes):
            errors.append("올바르지 않은 파일 데이터입니다")
        elif not self.validate_file_size(file_content):
            errors.append(f"파일 크기가 제한을 초과합니다 (최대 {self.max_file_size // (1024*1024)}MB)")
        
        if len(file_content) == 0:
            errors.append("빈 파일입니다")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
