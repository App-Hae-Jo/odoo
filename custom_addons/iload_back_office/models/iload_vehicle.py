# iload/models/iload_vehicle.py (기존 파일 수정)

from odoo import fields, models

class ILoadVehicle(models.Model):
    _name = 'iload.vehicle'
    _description = 'Iload 차량 정보'
    _order = 'name'

    name = fields.Char(string='차량 모델명', required=True, help="차량의 모델명 또는 설명 (예: 쏘나타, 싼타페, 1톤 트럭)")
    vehicle_type = fields.Selection([
        ('sedan', '세단'),
        ('hatchback', '해치백'),
        ('coupe', '쿠페'),
        ('suv', 'SUV'),
        ('truck', '트럭'),
        ('trailer', '트레일러'),
        ('motorcycle', '오토바이'),
        ('van', '밴'),
        ('ship', '선박'),
        ('plane', '항공기'),
        ('special', '특수 차량'),
        ('etc', '기타'),
    ], string='차량 유형', required=True, default='truck', help="차량의 대분류 및 세부 유형")
    is_active = fields.Boolean(string='활성', default=True, help="이 차량 모델이 현재 사용 가능한지 여부")
    description = fields.Text(string='설명')