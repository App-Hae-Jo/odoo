from odoo import models,fields, _

class IloadExportRecord(models.Model):
    _name = 'iload.export.record'
    _description = 'iLoad 수출 거래 장부'
    
    voucher_date = fields.Date(string='전표 작성일')
    company_name = fields.Char(string='거래 회사 이름')
    vehicle_name = fields.Char(string='차량명')
    mileage = fields.Integer(string='주행거리 (km)')
    license_plate = fields.Char(string='차량 번호')
    vin = fields.Char(string='차대 번호')
    car_year = fields.Integer(string='연식')
    release_price = fields.Float(string='출고가격(등록증)')
    purchase_price = fields.Float(string='구매금액(면장금액)')
    empty_weight = fields.Float(string='공차중량(kg)')
    length = fields.Float(string='길이')
    height = fields.Float(string='높이 (mm)')
    width = fields.Float(string='너비 (mm)')
    cbm = fields.Float(string='CBM')
    engine_displacement = fields.Integer(string='배기량 (cc)')
    fuel_type = fields.Selection([
        ('gasoline', 'Gasoline'),
        ('diesel', 'Diesel'),
        ('lpg', 'LPG'),
        ('lpi', 'LPI'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('hybrid_gasoline', 'Hybrid (Gasoline + Electric)'),
        ('hybrid_diesel', 'Hybrid (Diesel + Electric)'),
        ('hydrogen_electric', 'Hydrogen + Electric'),
        ('unknown', 'Unknown'),
    ], string='주유 구분')
    seating_capacity = fields.Integer(string='인승')
    modification = fields.Char(string='사양,튜닝 여부')
    export_country = fields.Char(string='수출 예정 또는 완료 국가')