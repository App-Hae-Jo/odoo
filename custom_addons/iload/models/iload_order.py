# iload/models/iload_order.py (수정)

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import date

class ILoadOrder(models.Model):
    _name = 'iload.order'
    _description = 'Iload 운송 주문'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # --- 기본 주문 정보 ---
    name = fields.Char(
        string='주문 번호',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default='New',
        help="주문을 구분하는 고유 참조 번호입니다. (YYYYMMDD-수출국가-일련번호)"
    )

    order_date = fields.Date(
        string='주문 일자',
        required=True,
        default=fields.Date.today(),
        help="주문이 생성된 날짜입니다."
    )

    # --- 고객사 정보 (res.partner 모델 연결) ---
    partner_id = fields.Many2one(
        'res.partner',
        string='고객사',
        required=True,
        domain="[('is_iload_customer', '=', True)]",
        help="이 운송 주문을 요청한 고객사"
    )
    receiver_partner_id = fields.Many2one(
        'res.partner',
        string='수취인/최종 목적지',
        help="화물을 최종적으로 수취할 파트너 (고객사와 다를 경우)"
    )
    contact_person_id = fields.Many2one(
        'res.partner',
        string='주문 담당자',
        domain="[('parent_id', '=', partner_id)]",
        help="이 주문을 담당하는 고객사 내의 담당자"
    )

    # --- 재무 정보 (res.currency 모델 연결) ---
    currency_id = fields.Many2one(
        'res.currency',
        string='통화',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
        help="주문의 총 금액에 사용될 통화입니다."
    )
    total_amount = fields.Monetary(
        string='총 주문 금액',
        currency_field='currency_id',
        compute='_compute_total_amount',
        store=True,
        help="이 주문의 총 금액 (모든 상세 라인 금액의 합계)입니다."
    )
    
    # --- 운송 주소 정보 (res.country 모델 연결) ---
    origin_address = fields.Char(string='출발지 주소', help="화물이 출발하는 주소입니다.")
    origin_country_id = fields.Many2one('res.country', string='출발 국가', help="화물이 출발하는 국가입니다.")
    destination_address = fields.Char(string='도착지 주소', help="화물이 도착할 최종 주소입니다.")
    destination_country_id = fields.Many2one(
        'res.country',
        string='수출 국가',
        required=True,
        help="화물이 최종적으로 도착할 국가입니다."
    )

    # --- 주문 상태 워크플로우 (order_detail_ids의 상태에 따라 계산됨) ---
    state = fields.Selection([
        ('draft', '초안'), # 주문이 생성되었지만 아직 상세 라인이 없거나 모두 초안일 때
        ('in_progress', '진행 중'), # 하나 이상의 상세 라인이 진행 중일 때
        ('partially_done', '부분 완료'), # 일부 상세 라인이 완료되었지만, 나머지는 진행 중이거나 취소/말소된 경우
        ('done', '완료됨'), # 모든 상세 라인이 인도 완료 또는 최종 취소/말소된 경우
        ('cancelled', '취소됨'), # 주문 자체가 취소된 경우 (모든 상세 라인 취소 포함)
    ], string='상태', compute='_compute_order_state', store=True, tracking=True)

    # --- 회사 컨텍스트 (Multi-company 환경에서 유용) ---
    company_id = fields.Many2one(
        'res.company',
        string='회사',
        required=True,
        default=lambda self: self.env.company,
        help="이 주문과 관련된 회사입니다."
    )

    # --- 주문 상세 라인 (One2many 관계) ---
    order_detail_ids = fields.One2many(
        'iload.order.detail',
        'order_id',
        string='주문 상세 라인',
        copy=True,
        help="이 주문에 포함된 각 차량에 대한 상세 정보입니다."
    )

    # --- 계산 필드 ---
    @api.depends('order_detail_ids.amount')
    def _compute_total_amount(self):
        """주문 상세 라인들의 금액 합계를 계산합니다."""
        for order in self:
            order.total_amount = sum(order.order_detail_ids.mapped('amount'))

    @api.depends('order_detail_ids.state')
    def _compute_order_state(self):
        """주문 상세 라인들의 상태를 기반으로 주문의 전체 상태를 계산합니다."""
        for order in self:
            if not order.order_detail_ids:
                order.state = 'draft' # 상세 라인이 없으면 초안
                continue

            all_detail_states = order.order_detail_ids.mapped('state')
            
            # 모든 상세 라인이 'draft'인 경우
            if all(state == 'draft' for state in all_detail_states):
                order.state = 'draft'
            # 모든 상세 라인이 'delivered', 'canceled', 'deregistered' 중 하나인 경우
            elif all(state in ('delivered', 'canceled', 'deregistered') for state in all_detail_states):
                # 모든 상세 라인이 'canceled' 또는 'deregistered'인 경우
                if all(state in ('canceled', 'deregistered') for state in all_detail_states):
                    order.state = 'cancelled' # 전체가 취소/말소된 경우
                else:
                    order.state = 'done' # 모든 라인이 완료(delivered)되었거나 취소/말소된 경우
            # 하나라도 'draft'가 아니고, 모든 상세가 완료/취소/말소 상태가 아닌 경우
            elif any(state not in ('draft', 'canceled', 'deregistered', 'delivered') for state in all_detail_states):
                 order.state = 'in_progress'
            # 일부만 완료되었거나 취소/말소된 경우 (나머지는 진행 중이 아님)
            elif any(state == 'delivered' for state in all_detail_states) and \
                 any(state in ('draft', 'vehicle_acquiring', 'customs_clearance', 'shipping') for state in all_detail_states):
                order.state = 'partially_done'
            else:
                order.state = 'in_progress' # 기본값으로 '진행 중' 설정 (만약 위에 해당하지 않는 복합 상태라면)


    # --- 생성 메서드 오버라이드 (주문 번호 자동 생성) ---
    @api.model
    def create(self, vals):
        """
        새로운 운송 주문 레코드를 생성하고, 주문 번호를 자동으로 생성합니다.
        주문 번호 형식: YYYYMMDD-(수출국가코드)-일련번호
        """
        if vals.get('name', 'New') == 'New':
            if not vals.get('destination_country_id'):
                raise ValidationError("주문 번호 생성을 위해 '수출 국가'를 먼저 선택해야 합니다.")

            destination_country = self.env['res.country'].browse(vals['destination_country_id'])
            today_str = date.today().strftime('%Y%m%d')
            country_code = destination_country.code.upper() if destination_country.code else 'XX'
            next_seq = self.env['ir.sequence'].next_by_code('iload.order.sequence') or '0000'
            vals['name'] = f"{today_str}-{country_code}-{next_seq}"

        return super().create(vals)

    # --- 상태 전환 액션 메서드 제거 (상세 라인에서 관리) ---
    # action_confirm_order, action_start_purchase 등 모든 action_ 메서드들을 제거합니다.
    # 이 메서드들은 이제 iload.order.detail에 정의되어야 합니다.