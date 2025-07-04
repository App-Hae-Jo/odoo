
import tempfile
import logging
from pathlib import Path
from .base_ocr import BaseOCRProcessor
from .image_processor import ImagePreprocessor
from .pdf_processor import PDFProcessor

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

_logger = logging.getLogger(__name__)

class PaddleOCRProcessor(BaseOCRProcessor):
    """🔍 PaddleOCR 구현체"""
    
    def __init__(self):
        self.supported_formats = {'.pdf', '.jpg', '.jpeg', '.png'}
        self.image_processor = ImagePreprocessor()
        self.pdf_processor = PDFProcessor()
        self._ocr_engine = None
    
    @property
    def ocr_engine(self):
        """지연 초기화된 OCR 엔진"""
        if self._ocr_engine is None:
            if PaddleOCR is None:
                raise ImportError("PaddleOCR이 설치되지 않았습니다")
            
            self._ocr_engine = PaddleOCR(
                use_angle_cls=True,
                lang='korean',
                use_gpu=False,
                show_log=False
            )
        return self._ocr_engine
    
    def extract_text(self, file_content: bytes, filename: str) -> str:
        """파일에서 텍스트 추출"""
        try:
            file_ext = Path(filename).suffix.lower()
            
            if file_ext == '.pdf':
                return self.pdf_processor.extract_text(file_content)
            elif file_ext in {'.jpg', '.jpeg', '.png'}:
                return self._extract_from_image(file_content)
            else:
                raise ValueError(f"지원되지 않는 파일 형식: {file_ext}")
                
        except Exception as e:
            _logger.error(f"텍스트 추출 실패: {e}")
            return ""
    
    def _extract_from_image(self, image_content: bytes) -> str:
        """이미지에서 텍스트 추출"""
        try:
            # 이미지 전처리
            processed_image = self.preprocess_image(image_content)
            
            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                tmp_file.write(processed_image)
                tmp_file.flush()
                
                # OCR 실행
                result = self.ocr_engine.ocr(tmp_file.name, cls=True)
                
                # 결과 처리
                text_lines = []
                if result and result[0]:
                    for line in result[0]:
                        if line and len(line) >= 2:
                            text_lines.append(line[1][0])
                
                # 임시 파일 삭제
                Path(tmp_file.name).unlink(missing_ok=True)
                
                return '\n'.join(text_lines)
                
        except Exception as e:
            _logger.error(f"이미지 OCR 처리 실패: {e}")
            return ""
    
    def is_supported_format(self, filename: str) -> bool:
        """지원되는 파일 형식인지 확인"""
        return Path(filename).suffix.lower() in self.supported_formats
    
    def preprocess_image(self, image_data: bytes) -> bytes:
        """이미지 전처리"""
        return self.image_processor.enhance_image(image_data)