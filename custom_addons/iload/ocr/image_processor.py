
import io
import logging
from PIL import Image, ImageEnhance, ImageFilter

_logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """🖼️ 이미지 전처리 클래스"""
    
    def __init__(self):
        self.max_size = (2000, 2000)
        self.quality = 95
        self.enhancement_settings = {
            'sharpness': 1.2,
            'contrast': 1.1,
            'brightness': 1.0,
            'color': 1.0
        }
    
    def enhance_image(self, image_data: bytes) -> bytes:
        """이미지 품질 향상"""
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # RGB 변환
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 크기 조정
                img = self._resize_image(img)
                
                # 품질 향상
                img = self._enhance_quality(img)
                
                # 노이즈 제거
                img = self._reduce_noise(img)
                
                # 바이트 변환
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=self.quality, optimize=True)
                return output.getvalue()
                
        except Exception as e:
            _logger.error(f"이미지 전처리 실패: {e}")
            return image_data
    
    def _resize_image(self, img: Image.Image) -> Image.Image:
        """이미지 크기 최적화"""
        # 너무 작은 이미지는 확대
        if img.size[0] < 800 or img.size[1] < 600:
            scale_factor = max(800 / img.size[0], 600 / img.size[1])
            new_size = (int(img.size[0] * scale_factor), int(img.size[1] * scale_factor))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # 너무 큰 이미지는 축소
        if img.size[0] > self.max_size[0] or img.size[1] > self.max_size[1]:
            img.thumbnail(self.max_size, Image.Resampling.LANCZOS)
        
        return img
    
    def _enhance_quality(self, img: Image.Image) -> Image.Image:
        """이미지 품질 향상"""
        try:
            # 선명도 향상
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(self.enhancement_settings['sharpness'])
            
            # 대비 향상
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(self.enhancement_settings['contrast'])
            
            # 밝기 조정
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(self.enhancement_settings['brightness'])
            
            return img
        except Exception as e:
            _logger.warning(f"이미지 품질 향상 실패: {e}")
            return img
    
    def _reduce_noise(self, img: Image.Image) -> Image.Image:
        """노이즈 제거"""
        try:
            # 가벼운 노이즈 제거 필터 적용
            img = img.filter(ImageFilter.MedianFilter(size=3))
            return img
        except Exception as e:
            _logger.warning(f"노이즈 제거 실패: {e}")
            return img