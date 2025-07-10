import logging
import sys
import fitz

logging.basicConfig(
    level=logging.INFO, # INFO 레벨로 조정하여 불필요한 DEBUG 메시지 감소
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('iload_vlm_inference.log'), # 로그 파일명 변경
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def convert_pdf_to_image(pdf_byte):
    """PDF를 이미지로 변환"""
    try:
         # PyMuPDF
        
        logger.info(" PDF → 이미지 변환 시작 (macOS)")
        pdf_doc = fitz.open(stream=pdf_byte, filetype="pdf")
        
        # 고해상도 변환 (macOS Retina 디스플레이 고려)
        page = pdf_doc[0] # 첫 페이지만 변환
        mat = fitz.Matrix(3.0, 3.0) # 해상도 조정 (3.0배 확대 - 이전보다 더 높임)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
            
        pdf_doc.close()
        
        logger.info(f"PDF 변환 완료: {len(img_data):,} bytes")
        return img_data
        
    except ImportError:
        logger.error("PyMuPDF가 설치되지 않았습니다. PDF 처리를 위해 'pip install PyMuPDF'를 실행해주세요.")
        return None
    except Exception as e:
        logger.error(f"PDF 변환 오류: {e}")
        return None