
import re
import logging
from typing import Dict, List, Tuple

_logger = logging.getLogger(__name__)

class DocumentValidator:
    """✅ 문서 데이터 검증자"""
    
    def __init__(self):
        self.valid_reasons = [
            '수출', '말소', '사고폐차', '해체', '폐기', 
            '분실', '도난', '폐차', '수출말소', '이전등록',
            '멸실', '훼손', '직권말소'
        ]
        
        # 차량번호 패턴들
        self.vehicle_patterns = [
            r'\d{2,3}[가-힣]\d{4}',                    # 12가3456, 123가4567
            r'[가-힣]{2,4}\d{2,3}[가-힣]\d{4}',        # 서울12가3456
            r'\d{2,3}\s*[가-힣]\s*\d{4}',             # 12 가 3456 (공백 포함)
            r'[가-힣]{2,4}\s*\d{2,3}\s*[가-힣]\s*\d{4}' # 서울 12 가 3456
        ]
        
        # 한글 이름 패턴
        self.name_pattern = r'^[가-힣]{2,4}
    
    def validate_extracted_data(self, data):
        """추출된 데이터 검증 및 정제"""
        validated = {}
        
        # 차량번호 검증
        vehicle_num = data.get('차량번호', '').strip() if data.get('차량번호') else ''
        validated['차량번호'] = self._validate_and_clean_vehicle_number(vehicle_num)
        
        # 소유자명 검증
        owner = data.get('소유자', '').strip() if data.get('소유자') else ''
        validated['소유자'] = self._validate_and_clean_owner_name(owner)
        
        # 말소사유 검증
        reason = data.get('말소사유', '').strip() if data.get('말소사유') else ''
        validated['말소사유'] = self._validate_and_clean_cancellation_reason(reason)
        
        return validated
    
    def _validate_and_clean_vehicle_number(self, vehicle_num):
        """차량번호 검증 및 정제"""
        if not vehicle_num:
            return None
        
        # 공백, 하이픈 제거 후 검증
        clean_num = re.sub(r'[\s\-]', '', vehicle_num)
        
        for pattern in self.vehicle_patterns:
            clean_pattern = pattern.replace(r'\s*', '')  # 패턴에서 공백 제거
            if re.match(f'^{clean_pattern}, clean_num):
                return clean_num
        
        # 패턴에 맞지 않지만 차량번호 형태인 경우 (부분 매칭)
        if re.search(r'\d+[가-힣]+\d+', clean_num):
            return clean_num
        
        return None
    
    def _validate_and_clean_owner_name(self, owner):
        """소유자명 검증 및 정제"""
        if not owner:
            return None
        
        # 한글만 추출
        korean_only = re.sub(r'[^가-힣]', '', owner)
        
        if re.match(self.name_pattern, korean_only):
            return korean_only
        
        # 2-4글자 한글이 포함되어 있다면 추출
        korean_match = re.search(r'[가-힣]{2,4}', owner)
        if korean_match:
            return korean_match.group()
        
        return None
    
    def _validate_and_clean_cancellation_reason(self, reason):
        """말소사유 검증 및 정제"""
        if not reason:
            return None
        
        # 정확히 일치하는 사유 찾기
        for valid_reason in self.valid_reasons:
            if valid_reason in reason:
                return valid_reason
        
        # 유사한 사유 찾기
        reason_mapping = {
            '폐차': ['폐차', '사고폐차', '폐기'],
            '수출': ['수출', '수출말소'],
            '말소': ['말소', '직권말소'],
            '해체': ['해체', '분해'],
            '분실': ['분실', '유실'],
            '도난': ['도난', '절도']
        }
        
        for main_reason, variations in reason_mapping.items():
            for variation in variations:
                if variation in reason:
                    return main_reason
        
        return None
    
    def calculate_confidence(self, data):
        """신뢰도 계산"""
        score = 0.0
        max_score = 3.0
        
        # 차량번호 점수 (가중치 높음 - 1.5점)
        vehicle_num = data.get('차량번호')
        if vehicle_num:
            if self._is_perfect_vehicle_number(vehicle_num):
                score += 1.5
            elif self._is_partial_vehicle_number(vehicle_num):
                score += 1.0
            else:
                score += 0.3
        
        # 소유자 점수 (1.0점)
        owner = data.get('소유자')
        if owner:
            if re.match(self.name_pattern, owner):
                score += 1.0
            else:
                score += 0.3
        
        # 말소사유 점수 (0.5점)
        reason = data.get('말소사유')
        if reason:
            if reason in self.valid_reasons:
                score += 0.5
            else:
                score += 0.2
        
        return min(score / max_score, 1.0)
    
    def _is_perfect_vehicle_number(self, vehicle_num):
        """완벽한 차량번호 형식인지 확인"""
        if not vehicle_num:
            return False
        
        clean_num = re.sub(r'[\s\-]', '', vehicle_num)
        perfect_patterns = [
            r'^\d{2,3}[가-힣]\d{4},
            r'^[가-힣]{2,4}\d{2,3}[가-힣]\d{4}
        ]
        
        return any(re.match(pattern, clean_num) for pattern in perfect_patterns)
    
    def _is_partial_vehicle_number(self, vehicle_num):
        """부분적으로 차량번호 형태인지 확인"""
        if not vehicle_num:
            return False
        
        # 숫자와 한글이 섞여있고 적절한 길이인지 확인
        has_number = bool(re.search(r'\d', vehicle_num))
        has_korean = bool(re.search(r'[가-힣]', vehicle_num))
        reasonable_length = 5 <= len(re.sub(r'[\s\-]', '', vehicle_num)) <= 12
        
        return has_number and has_korean and reasonable_length
    
    def get_validation_report(self, original_data, validated_data, confidence):
        """검증 보고서 생성"""
        report = {
            'confidence': confidence,
            'confidence_level': self._get_confidence_level(confidence),
            'issues': [],
            'suggestions': [],
            'field_status': {}
        }
        
        # 각 필드별 상태 확인
        for field in ['차량번호', '소유자', '말소사유']:
            original_value = original_data.get(field)
            validated_value = validated_data.get(field)
            
            if not original_value:
                status = 'missing'
                report['issues'].append(f'{field}가 추출되지 않았습니다')
            elif not validated_value:
                status = 'invalid'
                report['issues'].append(f'{field} 형식이 올바르지 않습니다: {original_value}')
            elif original_value != validated_value:
                status = 'modified'
                report['suggestions'].append(f'{field}가 정제되었습니다: {original_value} → {validated_value}')
            else:
                status = 'valid'
            
            report['field_status'][field] = {
                'status': status,
                'original': original_value,
                'validated': validated_value
            }
        
        return report
    
    def _get_confidence_level(self, confidence):
        """신뢰도 레벨 분류"""
        if confidence >= 0.8:
            return 'high'
        elif confidence >= 0.6:
            return 'medium'
        elif confidence >= 0.3:
            return 'low'
        else:
            return 'very_low'