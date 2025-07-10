
from odoo import models, fields, api
from datetime import datetime
import logging
from typing import List, Tuple, Dict, Any

_logger = logging.getLogger(__name__)

class DocumentRecord(models.Model):
    _name = 'iload.document.record'
    _description = '문서 처리 기록'
    _order = 'created_date desc'
    _rec_name = 'filename'
    
    # Selection 옵션을 상수로 정의 (타입 힌트 문제 해결)
    PROCESSING_METHOD_SELECTION = [
        ('pattern', '패턴 매칭'),
        ('gpt', 'OpenAI GPT'),
        ('claude', 'Anthropic Claude')
    ]
    
    # 기본 정보
    filename = fields.Char('파일명', required=True, index=True)
    file_content = fields.Binary('파일 내용', attachment=True)
    file_size = fields.Integer('파일 크기(bytes)', default=0)
    mime_type = fields.Char('MIME 타입', size=100)
    
    # 처리 정보
    extracted_text = fields.Text('추출된 텍스트')
    processing_method = fields.Selection(
        selection=PROCESSING_METHOD_SELECTION,
        string='처리 방법', 
        default='pattern', 
        required=True,
        index=True
    )
    confidence_score = fields.Float(
        '신뢰도', 
        digits=(3, 2), 
        default=0.0,
        help="0.0 ~ 1.0 사이의 신뢰도 점수"
    )
    processing_time = fields.Float(
        '처리 시간(초)', 
        digits=(5, 2),
        help="문서 처리에 소요된 시간"
    )
    
    # 추출된 정보
    vehicle_number = fields.Char(
        '차량번호', 
        index=True,
        help="추출된 차량 등록 번호"
    )
    owner_name = fields.Char(
        '소유자', 
        index=True,
        help="차량 소유자명"
    )
    cancellation_reason = fields.Char(
        '말소사유',
        help="차량 말소 사유"
    )
    
    # 메타데이터
    created_date = fields.Datetime(
        '생성일시', 
        default=fields.Datetime.now, 
        readonly=True,
        index=True
    )
    success = fields.Boolean(
        '성공 여부', 
        default=True,
        index=True
    )
    error_message = fields.Text('오류 메시지')
    user_id = fields.Many2one(
        'res.users', 
        '처리자', 
        default=lambda self: self.env.user,
        readonly=True
    )
    
    # 계산 필드
    confidence_percentage = fields.Float(
        '신뢰도(%)', 
        compute='_compute_confidence_percentage', 
        store=True,
        digits=(5, 1)
    )
    has_complete_info = fields.Boolean(
        '완전한 정보 여부', 
        compute='_compute_has_complete_info', 
        store=True
    )
    file_size_mb = fields.Float(
        '파일 크기(MB)',
        compute='_compute_file_size_mb',
        digits=(10, 2)
    )
    
    # 제약 조건
    _sql_constraints = [
        ('confidence_range', 
         'CHECK(confidence_score >= 0 AND confidence_score <= 1)', 
         '신뢰도는 0과 1 사이의 값이어야 합니다.'),
        ('positive_file_size', 
         'CHECK(file_size >= 0)', 
         '파일 크기는 0 이상이어야 합니다.'),
        ('positive_processing_time',
         'CHECK(processing_time >= 0)',
         '처리 시간은 0 이상이어야 합니다.')
    ]
    
    @api.depends('confidence_score')
    def _compute_confidence_percentage(self) -> None:
        """신뢰도 백분율 계산"""
        for record in self:
            record.confidence_percentage = record.confidence_score * 100
    
    @api.depends('vehicle_number', 'owner_name', 'cancellation_reason')
    def _compute_has_complete_info(self) -> None:
        """완전한 정보 여부 계산"""
        for record in self:
            record.has_complete_info = bool(
                record.vehicle_number and 
                record.owner_name and 
                record.cancellation_reason
            )
    
    @api.depends('file_size')
    def _compute_file_size_mb(self) -> None:
        """파일 크기를 MB 단위로 계산"""
        for record in self:
            record.file_size_mb = record.file_size / (1024 * 1024) if record.file_size else 0.0
    
    @api.model
    def create_from_processing_result(self, processing_data: Dict[str, Any]) -> 'DocumentRecord':
        """처리 결과로부터 레코드 생성
        
        Args:
            processing_data: 문서 처리 결과 데이터
            
        Returns:
            생성된 DocumentRecord 인스턴스
        """
        return self.create(processing_data)
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """처리 요약 통계
        
        Returns:
            처리 통계 딕셔너리
        """
        # 전체 처리 건수
        total_processed = self.search_count([])
        
        if total_processed == 0:
            return {
                'total_processed': 0,
                'success_rate': 0.0,
                'avg_confidence': 0.0,
                'processing_methods': {},
                'complete_info_rate': 0.0,
                'avg_processing_time': 0.0
            }
        
        # 성공 건수
        success_domain = [('success', '=', True)]
        success_count = self.search_count(success_domain)
        success_rate = (success_count / total_processed) * 100
        
        # 성공한 레코드들에 대한 통계
        success_records = self.search(success_domain)
        
        # 평균 신뢰도
        if success_records:
            avg_confidence = sum(success_records.mapped('confidence_score')) / len(success_records) * 100
            avg_processing_time = sum(success_records.mapped('processing_time')) / len(success_records)
        else:
            avg_confidence = 0.0
            avg_processing_time = 0.0
        
        # 처리 방법별 통계
        method_stats = {}
        for method_code, method_name in self.PROCESSING_METHOD_SELECTION:
            count = self.search_count([('processing_method', '=', method_code)])
            method_stats[method_code] = {
                'name': method_name,
                'count': count,
                'percentage': (count / total_processed * 100) if total_processed > 0 else 0
            }
        
        # 완전한 정보 추출률
        complete_info_count = self.search_count([('has_complete_info', '=', True)])
        complete_info_rate = (complete_info_count / total_processed) * 100
        
        return {
            'total_processed': total_processed,
            'success_rate': round(success_rate, 1),
            'avg_confidence': round(avg_confidence, 1),
            'processing_methods': method_stats,
            'complete_info_rate': round(complete_info_rate, 1),
            'avg_processing_time': round(avg_processing_time, 2)
        }
    
    def get_recent_records(self, limit: int = 10) -> 'DocumentRecord':
        """최근 처리 기록 조회
        
        Args:
            limit: 조회할 레코드 수
            
        Returns:
            최근 처리 기록들
        """
        return self.search([], limit=limit, order='created_date desc')
    
    def get_confidence_level(self) -> str:
        """신뢰도 레벨 문자열 반환
        
        Returns:
            신뢰도 레벨 ('high', 'medium', 'low', 'very_low')
        """
        self.ensure_one()
        
        if self.confidence_score >= 0.8:
            return 'high'
        elif self.confidence_score >= 0.6:
            return 'medium'
        elif self.confidence_score >= 0.3:
            return 'low'
        else:
            return 'very_low'
    
    def get_success_records_by_method(self) -> Dict[str, int]:
        """처리 방법별 성공 건수 조회
        
        Returns:
            처리 방법별 성공 건수 딕셔너리
        """
        result = {}
        for method_code, method_name in self.PROCESSING_METHOD_SELECTION:
            count = self.search_count([
                ('processing_method', '=', method_code),
                ('success', '=', True)
            ])
            result[method_code] = count
        
        return result
    
    def export_to_dict(self) -> Dict[str, Any]:
        """레코드를 딕셔너리로 내보내기
        
        Returns:
            레코드 데이터 딕셔너리
        """
        self.ensure_one()
        
        return {
            'id': self.id,
            'filename': self.filename,
            'file_size': self.file_size,
            'file_size_mb': self.file_size_mb,
            'processing_method': self.processing_method,
            'confidence_score': self.confidence_score,
            'confidence_percentage': self.confidence_percentage,
            'vehicle_number': self.vehicle_number,
            'owner_name': self.owner_name,
            'cancellation_reason': self.cancellation_reason,
            'processing_time': self.processing_time,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'success': self.success,
            'has_complete_info': self.has_complete_info,
            'confidence_level': self.get_confidence_level(),
            'error_message': self.error_message,
            'user_name': self.user_id.name if self.user_id else None,
        }
    
    @api.model
    def cleanup_old_records(self, days: int = 30) -> int:
        """오래된 레코드 정리
        
        Args:
            days: 보존할 일수
            
        Returns:
            삭제된 레코드 수
        """
        from datetime import timedelta
        
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_records = self.search([
            ('created_date', '<', cutoff_date),
            ('success', '=', False)  # 실패한 레코드만 삭제
        ])
        
        count = len(old_records)
        old_records.unlink()
        
        _logger.info(f"오래된 레코드 {count}개 삭제됨 (기준: {days}일 이전)")
        return count
    
    @api.model
    def get_processing_trends(self, days: int = 7) -> Dict[str, Any]:
        """최근 처리 트렌드 분석
        
        Args:
            days: 분석할 일수
            
        Returns:
            트렌드 분석 결과
        """
        from datetime import timedelta
        
        end_date = fields.Datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 기간 내 레코드 조회
        domain = [('created_date', '>=', start_date)]
        records = self.search(domain)
        
        if not records:
            return {
                'period_days': days,
                'total_processed': 0,
                'daily_average': 0.0,
                'success_trend': [],
                'confidence_trend': []
            }
        
        # 일별 통계 계산
        daily_stats = {}
        for record in records:
            date_key = record.created_date.date().isoformat()
            
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    'total': 0,
                    'success': 0,
                    'confidence_sum': 0.0,
                    'confidence_count': 0
                }
            
            daily_stats[date_key]['total'] += 1
            if record.success:
                daily_stats[date_key]['success'] += 1
                daily_stats[date_key]['confidence_sum'] += record.confidence_score
                daily_stats[date_key]['confidence_count'] += 1
        
        # 트렌드 데이터 생성
        success_trend = []
        confidence_trend = []
        
        for date_key, stats in sorted(daily_stats.items()):
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            avg_confidence = (stats['confidence_sum'] / stats['confidence_count'] * 100) if stats['confidence_count'] > 0 else 0
            
            success_trend.append({
                'date': date_key,
                'success_rate': round(success_rate, 1),
                'total_processed': stats['total']
            })
            
            confidence_trend.append({
                'date': date_key,
                'avg_confidence': round(avg_confidence, 1),
                'successful_processed': stats['success']
            })
        
        return {
            'period_days': days,
            'total_processed': len(records),
            'daily_average': round(len(records) / days, 1),
            'success_trend': success_trend,
            'confidence_trend': confidence_trend
        }