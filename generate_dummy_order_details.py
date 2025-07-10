
import csv
import random
from faker import Faker
from datetime import date, timedelta

fake = Faker('ko_KR')

def generate_dummy_order_details(num_records=40, order_ids=None, vehicle_ids=None, acquisition_ids=None):
    order_details_data = []
    
    if order_ids is None:
        order_ids = [f'order_iload_{i+1}' for i in range(20)] # 기본값으로 20개 가정
    if vehicle_ids is None:
        vehicle_ids = [f'vehicle_iload_{i+1}' for i in range(20)] # 기본값으로 20개 가정
    if acquisition_ids is None:
        acquisition_ids = [f'acquisition_iload_{i+1}' for i in range(20)] # 기본값으로 20개 가정

    fuel_types = ['G', 'D', 'LPG', 'EV', 'HY', 'ETC']

    for i in range(num_records):
        requested_delivery_date = fake.date_between(start_date='today', end_date='+6M')
        
        order_detail = {
            'id': f'order_detail_iload_{i+1}', # 외부 ID
            'order_id/id': random.choice(order_ids), # iload.order 참조
            'sequence': i + 1,
            'vehicle_id/id': random.choice(vehicle_ids), # iload.vehicle 참조
            'fuel_type': random.choice(fuel_types),
            'vehicle_year': str(random.randint(2010, 2024)),
            'acquisition_id/id': random.choice(acquisition_ids), # iload.vehicle.acquisition 참조
            'amount': round(random.uniform(1000000, 10000000), -3), # 1백만원 ~ 1천만원 단위
            'requested_delivery_date': requested_delivery_date.strftime('%Y-%m-%d'),
            'description': fake.text(max_nb_chars=100) if random.random() < 0.5 else '',
        }
        order_details_data.append(order_detail)
    
    return order_details_data

def write_to_csv(data, filename):
    if not data:
        print(f"No data to write to {filename}")
        return

    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    print(f"Successfully generated {len(data)} records in {filename}")

if __name__ == "__main__":
    # 각 참조 모델의 ID 목록을 실제 생성된 CSV 파일에서 읽어오는 것이 가장 정확합니다.
    # 여기서는 스크립트 실행 순서를 고려하여 임의의 ID 패턴을 가정합니다.
    order_ids = [f'order_iload_{i+1}' for i in range(20)] 
    vehicle_ids = [f'vehicle_iload_{i+1}' for i in range(20)] 
    acquisition_ids = [f'acquisition_iload_{i+1}' for i in range(20)] 

    order_details = generate_dummy_order_details(
        num_records=40, # 주문 상세는 주문보다 많을 수 있으므로 40개 생성
        order_ids=order_ids,
        vehicle_ids=vehicle_ids,
        acquisition_ids=acquisition_ids
    )
    write_to_csv(order_details, 'iload_order_detail_dummy_data.csv')
