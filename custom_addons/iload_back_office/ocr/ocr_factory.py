
import os
import sys
import base64
import logging
import json
import time
import io
import requests
import subprocess
import platform


# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, # INFO 레벨로 조정하여 불필요한 DEBUG 메시지 감소
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('iload_vlm_inference.log'), # 로그 파일명 변경
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class VLMProcessor:
    """ VLM 문서 처리기"""
    
    def __init__(self, model_type="ollama"):
        self.model_type = model_type
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "qwen2.5vl:7b" # 기본 LLaVA 7B 모델
        self.is_apple_silicon = self._check_apple_silicon()
        
        logger.info(f"🍎 macOS VLM 프로세서 초기화: {model_type}")
        logger.info(f"🔧 Apple Silicon: {'Yes' if self.is_apple_silicon else 'No'}")
        
        if model_type == "ollama":
            self._setup_ollama()
        elif model_type == "transformers":
            self._init_transformers_macos()
        else:
            logger.error(f"지원하지 않는 모델 타입: {model_type}. 'ollama' 또는 'transformers'를 사용하세요.")
            sys.exit(1) # 지원하지 않는 모델 타입이면 종료

    def _check_apple_silicon(self):
        """Apple Silicon (M1/M2/M3) 확인"""
        try:
            result = subprocess.run(['uname', '-m'], capture_output=True, text=True)
            return result.stdout.strip() == 'arm64'
        except Exception as e:
            logger.warning(f"Apple Silicon 확인 오류: {e}. 기본값으로 False 설정.")
            return False
    
    def _check_ollama_api(self):
        """Ollama API 연결 확인"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                logger.info(f"AI model name: {model_names}")
                return True
            else:
                logger.error(f"Ollama API Error: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.ConnectionError:
            logger.error(f"Ollama 서비스에 연결할 수 없습니다. 'ollama serve'가 실행 중인지 확인하세요.")
            return False
        except Exception as e:
            logger.error(f"Ollama API 연결 실패: {e}")
            return False
    
    def _check_and_download_model(self):
        """모델 확인 및 자동 다운로드"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            target_model_found = any(self.model_name in name for name in model_names)
            
            if not target_model_found:
                logger.warning(f" '{self.model_name}' 모델이 없습니다.")
                logger.info(f"'{self.model_name}' 모델 자동 다운로드 시작...")
                
                # 모델 다운로드
                download_cmd = ['ollama', 'pull', self.model_name]
                
                try:
                    # 다운로드 진행 상황을 실시간으로 보여주기 위해 stdout을 직접 연결
                    process = subprocess.Popen(download_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    for line in process.stdout:
                        print(line, end='') # 실시간 출력
                    process.wait() # 프로세스 종료 대기

                    if process.returncode == 0:
                        logger.info(f"'{self.model_name}' 다운로드 완료")
                        return True
                    else:
                        logger.error(f"모델 다운로드 실패: {process.stderr}")
                        logger.info(f"수동 다운로드: ollama pull {self.model_name}")
                        return False
                        
                except Exception as e:
                    logger.error(f"모델 다운로드 중 오류 발생: {e}")
                    logger.info(f" 수동 다운로드 권장: ollama pull {self.model_name}")
                    return False
            else:
                logger.info(f"'{self.model_name}' 모델 확인됨")
                return True
                
        except Exception as e:
            logger.error(f"모델 확인 오류: {e}")
            return False
    
    def _setup_ollama(self):
        """macOS용 Ollama 설정 및 서비스 확인"""
        # Ollama 서비스가 실행 중인지 확인하고, 아니면 시작 시도
        try:
            # pgrep으로 ollama 프로세스 확인
            result = subprocess.run(['pgrep', '-f', 'ollama serve'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ Ollama 서비스 실행 중입니다.")
            else:
                logger.info("🔄 Ollama 서비스가 실행되지 않았습니다. 자동 시작을 시도합니다...")
                # 백그라운드에서 ollama serve 실행
                subprocess.Popen(['ollama', 'serve'], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                
                # 서비스 시작 대기 및 연결 확인
                time.sleep(3) # 서비스 시작을 위한 짧은 대기
                if not self._check_ollama_api(): # API 연결 재확인
                    logger.error("Ollama 서비스 시작 실패 또는 연결 불가. 수동으로 'ollama serve'를 실행해주세요.")
                    sys.exit(1) # 서비스 시작 실패 시 스크립트 종료
                logger.info("Ollama 서비스 시작 성공.")
            
            # API 연결 확인 및 모델 다운로드
            if not self._check_ollama_api():
                sys.exit(1) # API 연결 실패 시 종료
            if not self._check_and_download_model():
                sys.exit(1) # 모델 다운로드 실패 시 종료
            
            logger.info("🎉 macOS Ollama 설정 완료!")
            
        except Exception as e:
            logger.error(f"Ollama 설정 중 오류 발생: {e}")
            logger.info("Ollama 설치 및 실행 상태를 확인해주세요.")
            sys.exit(1) # 오류 발생 시 스크립트 종료

    def _init_transformers_macos(self):
        """macOS용 Transformers 모델 초기화"""
        try:
            logger.info("Transformers 모델 로딩 중... (macOS 최적화)")
            
            from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration
            import torch
            from PIL import Image # PIL import 추가
            
            # Apple Silicon 최적화
            if self.is_apple_silicon:
                device = "mps" if torch.backends.mps.is_available() else "cpu"
                logger.info(f"Apple Silicon 감지 - 디바이스: {device}")
            else:
                device = "cpu"
                logger.info(f"Intel Mac - 디바이스: {device}")
            
            # 모델 로드
            model_name = "llava-hf/llava-v1.6-mistral-7b-hf"
            self.processor = LlavaNextProcessor.from_pretrained(model_name)
            self.model = LlavaNextForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if device == "mps" else torch.float32, # MPS에서는 float16 사용
                low_cpu_mem_usage=True
            ).to(device)
            
            logger.info("✅ Transformers 모델 로드 성공")
            
        except ImportError:
            logger.error("Transformers 또는 PyTorch가 설치되지 않았습니다.")
            logger.info("설치 필요: pip install transformers torch torchvision Pillow")
            self.model = None
            sys.exit(1) # 필수 라이브러리 없으면 종료
        except Exception as e:
            logger.error(f"Transformers 모델 로드 실패: {e}")
            self.model = None
            sys.exit(1) # 모델 로드 실패 시 종료
    
    def extract_fields(self, image_data):
        """VLM으로 필드 추출"""
        if self.model_type == "ollama":
            return self._extract_with_ollama(image_data)
        elif self.model_type == "transformers":
            return self._extract_with_transformers(image_data)
    
    def _extract_with_ollama(self, image_data):
        """Ollama VLM으로 필드 추출"""
        try:
            # 이미지를 base64로 인코딩
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # 한국어 문서 처리 최적화 프롬프트
            # JSON 스키마를 명확히 제시하여 모델이 일관된 형식으로 응답하도록 유도
            prompt = """
            이 문서 이미지를 분석하여 다음 JSON 스키마에 따라 정보를 추출해주세요.
            문서의 종류가 '자동차등록증'인 경우, 다음 필드들을 **문서 이미지에서 직접 읽어서** 추출하여 'extracted_data' 객체에 넣어주세요:
            '성명', '자동차 등록번호', '차명', '차종', '차대번호', '주행거리', '원동기형식'.
            **절대 예시 값을 사용하지 마세요. 문서에 있는 실제 텍스트를 정확히 추출해야 합니다.**
            만약 해당 필드가 문서에 없거나 식별하기 어렵다면, 해당 필드의 값은 빈 문자열("") 또는 null로 표시하세요. 해당 필드 자체를 JSON에서 제외하지 마세요.
            추출된 정보가 없거나 불확실한 경우에도 JSON 스키마를 지켜주세요.

            JSON 응답 형식:
            ```json
            {
                "document_type": "문서의 종류 (예: 자동차등록증, 신분증, 계약서, 영수증 등)",
                "extracted_data": {
                    // 여기에 문서에서 식별된 실제 필드명과 추출된 값을 넣어주세요.
                    // 예시: "성명": "김철수", "자동차 등록번호": "서울12가3456"
                    // 이 예시는 모델이 따라야 할 형식을 보여줄 뿐, 실제 추출 값은 이미지에서 찾아야 합니다.
                },
                "confidence": "전체 추출에 대한 신뢰도 (0.0 ~ 1.0 사이의 숫자)"
            }
            ```
            다른 설명 없이 JSON만 출력해주세요.
            """
            
            # Ollama API 호출
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [base64_image],
                "stream": False, # 스트리밍 비활성화
                "options": {
                    "temperature": 0.01, # 온도를 더 낮춰서 창의성 억제 및 일관성 강화
                    "top_p": 0.9,
                    "num_predict": 500 # 충분한 토큰 수
                }
            }
            
            logger.info("Ollama VLM API 호출 중...")
            response = requests.post(self.ollama_url, json=payload, timeout=120) # 타임아웃 증가
            
            if response.status_code != 200:
                raise Exception(f"API 응답 오류: {response.status_code} - {response.text}")
            
            result = response.json()
            response_text = result.get('response', '')
            
            logger.info(f"VLM 응답 길이: {len(response_text)} 문자")
            
            # JSON 추출 및 파싱
            extracted_data = self._parse_json_response(response_text)
            return extracted_data
            
        except requests.exceptions.Timeout:
            logger.error("Ollama VLM 처리 타임아웃. 모델이 너무 크거나 응답이 느릴 수 있습니다.")
            return {
                "document_type": "error",
                "extracted_data": {"error": "VLM 처리 타임아웃"},
                "confidence": 0.0
            }
        except Exception as e:
            logger.error(f"Ollama VLM 처리 오류: {e}")
            return {
                "document_type": "error",
                "extracted_data": {"error": str(e)},
                "confidence": 0.0
            }
    
    def _extract_with_transformers(self, image_data):
        """Transformers VLM으로 필드 추출"""
        if self.model is None:
            logger.error("Transformers 모델이 로드되지 않았습니다.")
            return {
                "document_type": "error", 
                "extracted_data": {"error": "모델이 로드되지 않음"},
                "confidence": 0.0
            }
        
        try:
            from PIL import Image
            import torch
            
            # 이미지 로드
            image = Image.open(io.BytesIO(image_data))
            
            # 프롬프트 (Ollama와 동일하게 JSON 스키마 명시)
            prompt = """
이 문서 이미지를 분석하여 다음 JSON 스키마에 따라 정보를 추출해주세요.
문서의 종류가 '자동차등록증'인 경우, 다음 필드들을 **문서 이미지에서 직접 읽어서** 추출하여 'extracted_data' 객체에 넣어주세요:
'성명', '자동차 등록번호', '차명', '차종', '차대번호', '주행거리', '원동기형식'.
**절대 예시 값을 사용하지 마세요. 문서에 있는 실제 텍스트를 정확히 추출해야 합니다.**
만약 해당 필드가 문서에 없거나 식별하기 어렵다면, 해당 필드의 값은 빈 문자열("") 또는 null로 표시하세요. 해당 필드 자체를 JSON에서 제외하지 마세요.
추출된 정보가 없거나 불확실한 경우에도 JSON 스키마를 지켜주세요.

JSON 응답 형식:
```json
{
    "document_type": "문서의 종류 (예: 자동차등록증, 신분증, 계약서, 영수증 등)",
    "extracted_data": {
        // 여기에 문서에서 식별된 실제 필드명과 추출된 값을 넣어주세요.
        // 예시: "성명": "김철수", "자동차 등록번호": "서울12가3456"
        // 이 예시는 모델이 따라야 할 형식을 보여줄 뿐, 실제 추출 값은 이미지에서 찾아야 합니다.
    },
    "confidence": "전체 추출에 대한 신뢰도 (0.0 ~ 1.0 사이의 숫자)"
}
```
다른 설명 없이 JSON만 출력해주세요.
"""
                        
            # 모델 입력 준비
            inputs = self.processor(prompt, image, return_tensors="pt")
            
            # Apple Silicon 최적화
            device = "mps" if self.is_apple_silicon and torch.backends.mps.is_available() else "cpu"
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # 추론
            logger.info("Transformers VLM 추론 중...")
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=400,
                    do_sample=False, # 결정론적 결과 유도
                    temperature=0.01 # 온도를 더 낮춰서 창의성 억제 및 일관성 강화
                )
            
            # 결과 디코딩
            response = self.processor.decode(outputs[0], skip_special_tokens=True)
            
            # JSON 추출 및 파싱
            extracted_data = self._parse_json_response(response)
            return extracted_data
            
        except Exception as e:
            logger.error(f"Transformers VLM 처리 오류: {e}")
            return {
                "document_type": "error",
                "extracted_data": {"error": str(e)},
                "confidence": 0.0
            }
    
    def _parse_json_response(self, response_text):
        """VLM 응답에서 JSON 추출 및 파싱"""
        try:
            # 코드 블록 내의 JSON을 처리하기 위해 ```json ... ``` 패턴 검사
            if '```json' in response_text:
                start_idx = response_text.find('```json') + len('```json')
                end_idx = response_text.rfind('```')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx].strip()
                else:
                    json_str = response_text.strip() # 코드 블록 없으면 전체 텍스트 시도
            else:
                # JSON 블록 찾기 (일반적인 { ... } 패턴)
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx == -1 or end_idx <= start_idx:
                    # JSON이 없으면 응답을 그대로 반환
                    logger.warning("응답에서 JSON 구조를 찾을 수 없습니다. 원시 응답을 반환합니다.")
                    return {
                        "document_type": "unknown",
                        "extracted_data": {"raw_response": response_text.strip()},
                        "confidence": 0.3
                    }
                json_str = response_text[start_idx:end_idx]
            
            logger.info(f"추출된 JSON 문자열:\n{json_str}")
            
            extracted_data = json.loads(json_str)
            
            # 필수 필드 검증 및 보완
            if not isinstance(extracted_data, dict):
                logger.warning("JSON이 객체 형태가 아닙니다. 'data' 필드에 래핑합니다.")
                extracted_data = {"data": extracted_data}
            
            if "extracted_data" not in extracted_data:
                extracted_data["extracted_data"] = {}
            
            if "document_type" not in extracted_data:
                extracted_data["document_type"] = "unknown"
            
            if "confidence" not in extracted_data:
                extracted_data["confidence"] = 0.8 # 기본 신뢰도
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}. 원시 응답: {response_text.strip()}")
            return {
                "document_type": "parse_error",
                "extracted_data": {"raw_response": response_text.strip(), "parse_error": str(e)},
                "confidence": 0.2
            }
        except Exception as e:
            logger.error(f"JSON 파싱 중 알 수 없는 오류 발생: {e}. 원시 응답: {response_text.strip()}")
            return {
                "document_type": "error",
                "extracted_data": {"error": str(e)},
                "confidence": 0.0
            }

def convert_pdf_to_image(file_data):
    """PDF를 이미지로 변환 (macOS 최적화)"""
    try:
        import fitz  # PyMuPDF
        
        logger.info("🔄 PDF → 이미지 변환 시작 (macOS)")
        pdf_doc = fitz.open(stream=file_data, filetype="pdf")
        
        # 고해상도 변환 (macOS Retina 디스플레이 고려)
        page = pdf_doc[0] # 첫 페이지만 변환
        mat = fitz.Matrix(3.0, 3.0) # 해상도 조정 (3.0배 확대 - 이전보다 더 높임)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        
        # 디버깅용 이미지 저장 (선택 사항)
        # desktop_path = os.path.expanduser("~/Desktop")
        # debug_file = f"{desktop_path}/debug_pdf_conversion_{int(time.time())}.png"
        # with open(debug_file, "wb") as f:
        #     f.write(img_data)
        # logger.info(f"🖼️ 디버깅 이미지 저장: {debug_file}")
            
        pdf_doc.close()
        
        logger.info(f"✅ PDF 변환 완료: {len(img_data):,} bytes")
        return img_data
        
    except ImportError:
        logger.error("❌ PyMuPDF가 설치되지 않았습니다. PDF 처리를 위해 'pip install PyMuPDF'를 실행해주세요.")
        return None
    except Exception as e:
        logger.error(f"PDF 변환 오류: {e}")
        return None

def main():
    """메인 함수: 지정된 PDF 파일을 VLM으로 처리하고 결과를 출력합니다."""
    print("🍎 iLoad VLM 추론 스크립트 (macOS 최적화)")
    print("=" * 60)
    print("성능 테스트를 위해 지정된 PDF 파일에서 VLM을 사용하여 정보를 추출합니다.")
    print()
    
    # macOS 확인
    if platform.system() != 'Darwin':
        print("❌ 이 스크립트는 macOS 전용입니다.")
        sys.exit(1)
    
    # 모델 선택 (기본값: ollama)
    model_type = "ollama" # 또는 "transformers"
    print(f"🤖 사용할 VLM: {model_type}")
    
    if model_type == "ollama":
        print("💡 Ollama 사용 시 다음 사항을 확인해주세요:")
        print("  1. Ollama가 설치되어 있어야 합니다. (brew install ollama)")
        print("  2. 'ollama serve' 서비스가 실행 중이어야 합니다. (스크립트가 자동 시작 시도)")
        print(f"  3. '{VLMProcessor().model_name}' 모델이 다운로드되어 있어야 합니다. (스크립트가 자동 다운로드 시도)")
        print()
    elif model_type == "transformers":
        print("💡 Transformers 사용 시 다음 사항을 확인해주세요:")
        print("  1. 'transformers', 'torch', 'Pillow' 라이브러리가 설치되어 있어야 합니다. (pip install transformers torch torchvision Pillow)")
        print("  2. 모델 파일 다운로드가 필요할 수 있습니다.")
        print()

    # 고정된 파일 경로 사용 (성능 테스트용)
    home_dir = os.path.expanduser("~")
    # 아래 경로를 실제 사용자 이름에 맞게 수정해주세요.
    file_path = f"{home_dir}/Downloads/08도6796_275966.pdf" 
    
    if not os.path.exists(file_path):
        print(f"❌ 지정된 파일 '{file_path}'을 찾을 수 없습니다. 경로를 확인하거나 파일을 다운로드 폴더에 넣어주세요.")
        sys.exit(1)
    
    file_name = os.path.basename(file_path)
    file_extension = os.path.splitext(file_path)[1].lower()
    
    print(f"\n📄 처리할 파일: {file_name}")
    print(f"📏 파일 크기: {os.path.getsize(file_path):,} bytes")
    print(f"🏷️ 파일 확장자: {file_extension}")
    print("\n" + "=" * 60)
    
    # VLM 프로세서 초기화
    vlm_processor = VLMProcessor(model_type=model_type)
    
    # 파일 데이터 읽기
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    image_data = None
    processing_method = ""

    # 이미지 데이터 준비
    if file_extension == '.pdf':
        print("PDF 파일입니다. 이미지로 변환합니다...")
        image_data = convert_pdf_to_image(file_data)
        if image_data is None:
            print("❌ PDF 변환에 실패했습니다. 스크립트를 종료합니다.")
            sys.exit(1)
        processing_method = "PDF → Image → VLM"
    elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
        print("이미지 파일입니다. 직접 VLM으로 처리합니다...")
        image_data = file_data
        processing_method = "Image → VLM"
    else:
        print(f"❌ 지원하지 않는 파일 형식입니다: {file_extension}. PDF 또는 이미지 파일을 제공해주세요.")
        sys.exit(1)

    # VLM 처리 시작
    print("\n🤖 VLM 필드 추출을 시작합니다...")
    start_time = time.time()
    result = vlm_processor.extract_fields(image_data)
    end_time = time.time()
    processing_time = end_time - start_time
    
    # 결과 출력
    print("\n" + "=" * 60)
    print("📊 VLM 처리 결과:")
    print("=" * 60)
    print(f"  🔧 처리 방법: {processing_method}")
    print(f"  ⏱️ 총 처리 시간: {processing_time:.2f}초")
    print(f"  📄 문서 타입: {result.get('document_type', 'unknown')}")
    print(f"  🎯 신뢰도: {result.get('confidence', 0.0):.2%}")
    
    extracted_data = result.get('extracted_data', {})
    if extracted_data:
        print(f"  📋 추출된 데이터 ({len(extracted_data)}개):")
        for key, value in extracted_data.items():
            # 긴 텍스트는 줄임 처리하여 출력
            if isinstance(value, str) and len(value) > 100:
                print(f"    - {key}: {value[:100]}...")
            else:
                print(f"    - {key}: {value}")
    else:
        print("  ⚠️ 추출된 데이터가 없습니다.")
        if "raw_response" in result.get('extracted_data', {}):
            print(f"  Raw 응답: {result['extracted_data']['raw_response']}")
        if "error" in result.get('extracted_data', {}):
            print(f"  오류: {result['extracted_data']['error']}")
    
    print("\n🎉 VLM 처리 완료!")

if __name__ == "__main__":
    main()
