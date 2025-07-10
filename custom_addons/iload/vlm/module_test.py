import sys
import platform
import os
import time

from .ocr_factory import VLMProcessor
from .convert_image import convert_pdf_to_image


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
