import odoo
from odoo import api, SUPERUSER_ID

# generate_dummy_data.py
# Run this script in Odoo shell:
# ./odoo-bin shell -d your_database_name < generate_dummy_data.py

from datetime import date, timedelta
import random

print("--- Starting Dummy Data Generation ---")

# Initialize env for script execution
# This part is crucial for 'env' to be defined when running via redirection
if 'env' not in locals():
    registry = odoo.modules.registry.Registry.new(odoo.tools.config['db_name'])
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

# --- Helper function to get random partner ---
def get_random_partner(is_customer=None, parent_id=None):
    domain = []
    if is_customer is not None:
        domain.append(('is_iload_customer', '=', is_customer))
    if parent_id is not None:
        domain.append(('parent_id', '=', parent_id))
    
    partners = env['res.partner'].search(domain)
    if not partners:
        print(f"Warning: No partners found for domain {domain}. Skipping.")
        return None
    return random.choice(partners)

# --- Helper function to get random vehicle ---
def get_random_vehicle():
    vehicles = env['iload.vehicle'].search([])
    if not vehicles:
        print("Warning: No vehicles found. Skipping.")
        return None
    return random.choice(vehicles)

# --- Helper function to get random country ---
def get_random_country():
    # Search for some common countries
    countries = env['res.country'].search([('code', 'in', ['KR', 'US', 'CN', 'JP', 'DE', 'VN'])])
    if not countries:
        # Fallback to any country if specific ones are not found
        countries = env['res.country'].search([], limit=10) 
    if not countries:
        print("Warning: No countries found. Skipping.")
        return None
    return random.choice(countries)

# 1. Generate res.partner (Customers and Contacts)
print("1. Generating res.partner (Customers and Contacts)...")
partners_data = [
    {'name': '아이로드 고객사 A', 'is_iload_customer': True, 'iload_customer_code': 'CUST001', 'email': 'customerA@example.com', 'phone': '02-1234-5678', 'currency_id': env.company.currency_id.id, 'destination_country_id': get_random_country().id if get_random_country() else False},
    {'name': '아이로드 고객사 B', 'is_iload_customer': True, 'iload_customer_code': 'CUST002', 'email': 'customerB@example.com', 'phone': '031-9876-5432', 'currency_id': env.company.currency_id.id, 'destination_country_id': get_random_country().id if get_random_country() else False},
    {'name': '아이로드 고객사 C', 'is_iload_customer': True, 'iload_customer_code': 'CUST003', 'email': 'customerC@example.com', 'phone': '051-1111-2222', 'currency_id': env.company.currency_id.id, 'destination_country_id': get_random_country().id if get_random_country() else False},
    {'name': '일반 수취인 D', 'is_iload_customer': False, 'email': 'receiverD@example.com', 'phone': '070-1111-3333'},
    {'name': '일반 수취인 E', 'is_iload_customer': False, 'email': 'receiverE@example.com', 'phone': '070-2222-4444'},
    {'name': '판매처 주식회사 ABC', 'is_iload_customer': False, 'email': 'sellerABC@example.com', 'phone': '02-5555-6666'},
    {'name': '개인 판매자 김민준', 'is_iload_customer': False, 'email': 'kimminjun@example.com', 'phone': '010-4444-5555'},
]

for data in partners_data:
    try:
        partner = env['res.partner'].create(data)
        print(f"Created Partner: {partner.name} (ID: {partner.id})")
    except Exception as e:
        print(f"Error creating partner {data['name']}: {e}")

# Create contacts for customers
customer_a = env['res.partner'].search([('name', '=', '아이로드 고객사 A')], limit=1)
if customer_a:
    contact_a1 = env['res.partner'].create({'name': '김철수 (고객사 A 담당자)', 'parent_id': customer_a.id, 'email': 'kimcs@example.com', 'phone': '010-1111-1111'})
    contact_a2 = env['res.partner'].create({'name': '이영희 (고객사 A 담당자)', 'parent_id': customer_a.id, 'email': 'leeyh@example.com', 'phone': '010-2222-2222'})
    print(f"Created Contact: {contact_a1.name} (ID: {contact_a1.id}) for {customer_a.name}")
    print(f"Created Contact: {contact_a2.name} (ID: {contact_a2.id}) for {customer_a.name}")

customer_b = env['res.partner'].search([('name', '=', '아이로드 고객사 B')], limit=1)
if customer_b:
    contact_b1 = env['res.partner'].create({'name': '박지성 (고객사 B 담당자)', 'parent_id': customer_b.id, 'email': 'parkjs@example.com', 'phone': '010-3333-3333'})
    print(f"Created Contact: {contact_b1.name} (ID: {contact_b1.id}) for {customer_b.name}")

# 2. Generate iload.vehicle (Vehicle Models)
print("2. Generating iload.vehicle (Vehicle Models)...")
vehicles_data = [
    {'name': '현대 쏘나타', 'vehicle_type': 'sedan', 'description': '인기 있는 중형 세단'},
    {'name': '기아 쏘렌토', 'vehicle_type': 'suv', 'description': '패밀리 SUV'},
    {'name': '현대 포터 II', 'vehicle_type': 'truck', 'description': '1톤 소형 트럭'},
    {'name': '테슬라 모델 3', 'vehicle_type': 'etc', 'description': '전기차'}, # Assuming 'etc' for EV
    {'name': 'BMW 520d', 'vehicle_type': 'sedan', 'description': '수입 디젤 세단'},
    {'name': '벤츠 E클래스', 'vehicle_type': 'sedan', 'description': '고급 세단'},
    {'name': '쉐보레 콜로라도', 'vehicle_type': 'truck', 'description': '픽업 트럭'},
]

for data in vehicles_data:
    try:
        vehicle = env['iload.vehicle'].create(data)
        print(f"Created Vehicle: {vehicle.name} (ID: {vehicle.id})")
    except Exception as e:
        print(f"Error creating vehicle {data['name']}: {e}")

# 3. Generate iload.vehicle.acquisition (Vehicle Acquisitions)
print("3. Generating iload.vehicle.acquisition (Vehicle Acquisitions)...")
acquisition_count = 10
created_acquisitions = []
for i in range(acquisition_count):
    seller_name = random.choice(['판매처 주식회사 ABC', '개인 판매자 김민준', '중고차 딜러 이수진'])
    seller_reg_no = f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(10000,99999)}" if "주식회사" in seller_name else f"{random.randint(100000,999999)}-{random.randint(1000000,9999999)}"
    seller_address = random.choice(['서울 강남구 테헤란로 123', '경기 성남시 분당구 판교역로 123', '부산 해운대구 센텀시티로 123'])
    seller_phone = f"010-{random.randint(1000,9999)}-{random.randint(1000,9999)}"

    vehicle = get_random_vehicle()
    if not vehicle:
        continue

    acquisition_date = date.today() - timedelta(days=random.randint(1, 365))
    car_reg_num = f"{random.choice(['서울', '경기', '부산'])}{random.randint(10,99)}{random.choice(['가', '나', '다', '라'])}{random.randint(1000,9999)}"
    chassis_num = f"KOR{random.randint(10000000000000,99999999999999)}" # Unique chassis number
    acquisition_amount = random.randint(5000000, 50000000)
    currency = env['res.currency'].search([('name', '=', 'KRW')], limit=1) or env.company.currency_id
    fuel_type = random.choice(['G', 'D', 'LPG', 'EV', 'HY', 'ETC'])

    try:
        acquisition = env['iload.vehicle.acquisition'].create({
            'acquisition_date': acquisition_date,
            'acquisition_from_type': 'corporate' if "주식회사" in seller_name else 'individual',
            'seller_name': seller_name,
            'seller_registration_no': seller_reg_no,
            'seller_address': seller_address,
            'seller_contact_person': f"{seller_name} 담당자",
            'seller_phone': seller_phone,
            'car_registration_number': car_reg_num,
            'chassis_number': chassis_num,
            'vehicle_id': vehicle.id,
            'english_vehicle_name': vehicle.name, # Use vehicle name as English name for simplicity
            'mileage': random.randint(1000, 150000),
            'vehicle_weight': random.randint(1000, 3000),
            'engine_displacement': random.randint(1000, 5000),
            'acquisition_amount': acquisition_amount,
            'acquisition_currency_id': currency.id,
            'storage_location': random.choice(['본사 창고', '부산 야적장', '인천 보세창고']),
            'deregistration_status': random.choice([True, False]),
            'deregistration_date': date.today() - timedelta(days=random.randint(1, 30)) if random.choice([True, False]) else False,
            'fuel_type': fuel_type,
        })
        created_acquisitions.append(acquisition)
        print(f"Created Acquisition: {acquisition.name} (Chassis: {acquisition.chassis_number})")
    except Exception as e:
        print(f"Error creating acquisition: {e}")

# 4. Generate iload.order (Orders) and iload.order.detail (Order Details)
)
order_count = 5
for i in range(order_count):
    customer = get_random_partner(is_customer=True)
    if not customer:
        continue
    
    receiver = get_random_partner(is_customer=False)
    contact = env['res.partner'].search([('parent_id', '=', customer.id)], limit=1) or customer # Fallback to customer if no specific contact

    origin_country = get_random_country()
    destination_country = get_random_country()
    if not origin_country or not destination_country:
        continue

    order_date = date.today() - timedelta(days=random.randint(1, 90))
    
    try:
        order = env['iload.order'].create({
            'order_date': order_date,
            'partner_id': customer.id,
            'receiver_partner_id': receiver.id if receiver else False,
            'contact_person_id': contact.id if contact else False,
            'currency_id': env.company.currency_id.id,
            'origin_address': random.choice(['서울 강남구', '부산 해운대구', '인천 연수구']),
            'origin_country_id': origin_country.id,
            'destination_address': random.choice(['도쿄', '뉴욕', '베를린', '호치민']),
            'destination_country_id': destination_country.id,
        })
        print(f"Created Order: {order.name} (Customer: {customer.name})")

        # Generate order details for this order
        num_details = random.randint(1, 3) # 1 to 3 details per order
        for j in range(num_details):
            vehicle = get_random_vehicle()
            if not vehicle:
                continue
            
            # Try to find an unlinked acquisition
            available_acquisitions = env['iload.vehicle.acquisition'].search([('order_detail_id', '=', False)])
            acquisition = random.choice(available_acquisitions) if available_acquisitions else None

            if not acquisition:
                print(f"Warning: No unlinked acquisitions available for order detail. Skipping detail for order {order.name}.")
                continue

            requested_delivery_date = order_date + timedelta(days=random.randint(15, 60))
            amount = random.randint(1000000, 10000000)

            try:
                order_detail = env['iload.order.detail'].create({
                    'order_id': order.id,
                    'sequence': (j + 1) * 10,
                    'vehicle_id': vehicle.id,
                    'fuel_type': acquisition.fuel_type if acquisition else random.choice(['G', 'D', 'LPG', 'EV', 'HY', 'ETC']),
                    'vehicle_year': str(random.randint(2010, 2024)),
                    'acquisition_id': acquisition.id,
                    'amount': amount,
                    'requested_delivery_date': requested_delivery_date,
                    'state': random.choice(['draft', 'vehicle_acquiring', 'customs_clearance_prep', 'delivered']),
                    'description': f"주문 상세 {j+1}에 대한 설명",
                })
                print(f"  Created Order Detail for {order.name}: {order_detail.display_name}")
            except Exception as e:
                print(f"  Error creating order detail for order {order.name}: {e}")

    except Exception as e:
        print(f"Error creating order: {e}")

print("--- Dummy Data Generation Complete ---")