
import os
import sys
import base64
import logging
import json
import time
import io
import requests
import subprocess


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
                low_cpu_mem_usage=True,
                device_map=device
            )
            
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
            return self._extract_with_ollama(image_data, docs_type=None)
        elif self.model_type == "transformers":
            return self._extract_with_transformers(image_data)
    
    def _extract_with_ollama(self, image_data, docs_type):
        """Ollama VLM으로 필드 추출"""
        try:
            # 이미지를 base64로 인코딩
            base64_image = base64.b64encode(image_data).decode('utf-8')
            # 한국어 문서 처리 최적화 프롬프트
            # JSON 스키마를 명확히 제시하여 모델이 일관된 형식으로 응답하도록 유도
            prompt = """
            이 문서 이미지를 분석하여 다음 JSON 스키마에 따라 정보를 추출해주세요.  
            문서의 종류가 '자동차등록증' 또는 이와 관련된 차량 매입 문서일 경우, 아래의 모든 필드를 **문서 이미지에서 직접 읽은 실제 값으로** 추출하여 'extracted_data'에 넣어주세요.  

            ❗ 반드시 주의사항:
            - 예시 값을 생성하지 마세요. **문서 내 실제 값**만 추출하십시오.
            - 값이 없는 항목도 키는 유지하고, 해당 값은 `null` 또는 `""`로 표기하십시오.
            - **날짜 필드 (acquisition_date, deregistration_date)는 반드시 'YYYY-MM-DD' 형식으로 추출해주세요.**
            - 필드를 생략하지 말고 아래 스키마에 나온 순서와 키 이름을 **정확히 지켜주세요.**
            - 전체 필드에 대한 신뢰도(confidence)는 0.0 ~ 1.0 사이로 추정해주세요.
            - 숫자가 있는 값은 단위를 추가하지 마십시오.(원, km 등) db 입력을 위해 float 으로 유지해주세요.
            - 숫자가 있는 값은 쉼표를 추가하지 마십시오. db 입력을 위해 쉼표 없이 숫자만 유지해주세요.
            - 소유자 명칭을 확인하여 seller_contact_person 을 확인하시고 개인사업자와, 법인사업자, 개인이 주체가 되는지 확인이필요합니다
            - 소유자 명칭을 확인하여서 주체가 회사이름 이라면 법인, 개인 중 사업자라면 개인, 개인이라면 개인으로 처리하여 주체를 나누어주세요.
            추출할 필드 목록은 다음과 같습니다 (key명은 영문 그대로 사용):
            - "차대번호는 정확히 17자리의 영문 대문자와 숫자 조합입니다. 전화번호처럼 보일 수 있지만, 절대 연락처로 인식하지 마세요. 공백이나 하이픈 없이 연결된 코드이며, 'I', 'O', 'Q'는 포함되지 않습니다."
            - 주행거리는 자동차가 지금까지 달린 누적 거리로 일반적으로 단위는 'km'이며, 보통 수천에서 수십만 사이의 값으로 나타나며 'mm'와 같은 차량 제원 단위와 혼동하지 말고, 자동차 등록증의 검사 유효기간 근처에 위치합니다. 해당 위치에 없다면 기입하지 말아주세요.
            - 차량 무게(kg), 너비(mm), 배기량(cc)는 자동차의 제원(사양) 정보로, 각각 1000~3500kg, 1500~2200mm, 1000~5000cc 범위이며 주행거리나 연락처 등과 절대 혼동하지 마세요.

            ```json
            {
            "name": "",
            "acquisition_date": "", <-- 여기에 'YYYY-MM-DD' 형식을 설명합니다.
            "acquisition_from_type": "", <- 여기에 주체를 확인하여 ('corporate', 'sole_proprietor', 'individual') 중에 선택해서 넣어주세요
            "seller_name": "", <- 여기에 소유자 명칭을 설명합니다.
            "seller_registration_no": "",
            "seller_address": "",
            "seller_contact_person": "",
            "seller_phone": "",
            "car_registration_number": "",
            "chassis_number": "", <- 여기에 차대 번호를 설명합니다
            "english_vehicle_name": "", 
            "mileage": "", <- 여기에 주행 거리를 설명합니다
            "vehicle_weight": "", <- 여기에 차량 무게를 설명합니다.
            "engine_displacement": "", <- 여기에 배기량을 설명합니다. 
            "acquisition_amount": "", <-- 여기에 ','가 있다면 ,만 제거해서 숫자값만 넣어주세요
            "acquisition_currency_id": "",
            "storage_location": "",
            "deregistration_status": "",
            "deregistration_date": "", <-- 여기에 'YYYY-MM-DD' 형식을 설명합니다.
            "fuel_type": ""
            }
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