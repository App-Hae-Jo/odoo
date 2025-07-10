
class PromptManager:
    """📝 프롬프트 관리자"""
    
    def __init__(self):
        self.base_prompt_template = """당신은 차량 관련 문서에서 정보를 추출하는 전문가입니다.
다음 텍스트에서 차량 정보를 정확히 추출해주세요.

추출할 정보:
1. 차량번호: 한국 차량번호 형식 (예: "12가3456", "서울12가3456")
2. 소유자: 한글 이름만 (예: "홍길동", "김철수")  
3. 말소사유: 차량 말소 사유 (예: "수출", "사고폐차", "해체", "폐기")

문서 텍스트:
{text}

다음 JSON 형식으로만 응답해주세요. 정보가 없으면 null을 사용하세요:
{{
    "차량번호": "추출된 차량번호 또는 null",
    "소유자": "추출된 소유자명 또는 null",
    "말소사유": "추출된 말소사유 또는 null"
}}"""
    
    def create_vehicle_extraction_prompt(self, text):
        """차량 정보 추출용 프롬프트 생성"""
        return self.base_prompt_template.format(text=text)
    
    def create_validation_prompt(self, extracted_data, original_text):
        """추출 결과 검증용 프롬프트 생성"""
        return f"""다음은 문서에서 추출된 정보입니다. 원본 텍스트와 비교하여 정확성을 검증해주세요.

추출된 정보:
- 차량번호: {extracted_data.get('차량번호', 'null')}
- 소유자: {extracted_data.get('소유자', 'null')}
- 말소사유: {extracted_data.get('말소사유', 'null')}

원본 텍스트:
{original_text}

각 정보가 원본 텍스트와 일치하는지 확인하고, 수정이 필요한 경우 올바른 정보를 제공해주세요.
JSON 형식으로 응답해주세요."""
    
    def create_structured_prompt(self, text, document_type="vehicle_document"):
        """문서 타입별 구조화된 프롬프트 생성"""
        prompts = {
            "vehicle_document": self.base_prompt_template,
            "cancellation_certificate": """차량 말소등록증에서 다음 정보를 추출해주세요:
            
문서 텍스트: {text}

JSON 형식으로 응답:
{{
    "차량번호": "차량등록번호",
    "소유자": "소유자 성명",
    "말소사유": "말소 사유",
    "말소일자": "말소 처리 일자",
    "발급기관": "발급 기관명"
}}""",
            "export_certificate": """수출용 차량 서류에서 다음 정보를 추출해주세요:
            
문서 텍스트: {text}

JSON 형식으로 응답:
{{
    "차량번호": "차량등록번호", 
    "소유자": "소유자 성명",
    "말소사유": "수출",
    "목적지": "수출 목적지",
    "수출업체": "수출업체명"
}}"""
        }
        
        template = prompts.get(document_type, self.base_prompt_template)
        return template.format(text=text)