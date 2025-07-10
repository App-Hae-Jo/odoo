
import csv
import random
from faker import Faker
from datetime import date, timedelta

fake = Faker('ko_KR')

def generate_dummy_acquisitions(num_records=20, vehicle_ids=None):
    acquisitions_data = []
    
    if vehicle_ids is None:
        vehicle_ids = [f'vehicle_iload_{i+1}' for i in range(20)] # 기본값으로 20개 가정

    fuel_types = ['G', 'D', 'LPG', 'EV', 'HY', 'ETC']
    
    for i in range(num_records):
        acquisition_date = fake.date_between(start_date='-2y', end_date='today')
        deregistration_status = random.choice([True, False, False, False]) # 25% 확률로 말소
        deregistration_date = acquisition_date + timedelta(days=random.randint(30, 365)) if deregistration_status else ''

        acquisition = {
            'id': f'acquisition_iload_{i+1}', # 외부 ID
            'name': f'ACQ{random.randint(100000, 999999)}', # 임의의 매입 번호
            'acquisition_date': acquisition_date.strftime('%Y-%m-%d'),
            'acquisition_from_type': random.choice(['corporate', 'individual']),
            'seller_name': fake.company() if random.random() < 0.7 else fake.name(),
            'seller_registration_no': fake.ssn() if random.random() < 0.7 else '',
            'seller_address': fake.address(),
            'seller_contact_person': fake.name(),
            'seller_phone': fake.phone_number(),
            'car_registration_number': f'{random.randint(10,99)}가{random.randint(1000,9999)}', # 임의의 자동차등록번호
            'chassis_number': fake.unique.vin(), # 고유한 차대 번호
            'vehicle_id/id': random.choice(vehicle_ids), # iload.vehicle 참조
            'english_vehicle_name': fake.word().capitalize() + ' ' + fake.word().capitalize(),
            'mileage': round(random.uniform(1000, 200000), 2),
            'vehicle_weight': round(random.uniform(1000, 5000), 2),
            'engine_displacement': round(random.uniform(1000, 5000), 2),
            'acquisition_amount': round(random.uniform(5000000, 50000000), -3), # 5백만원 ~ 5천만원 단위
            'acquisition_currency_id/name': random.choice(['KRW', 'USD', 'EUR']), # 통화 코드
            'storage_location': fake.address(),
            'deregistration_status': deregistration_status,
            'deregistration_date': deregistration_date.strftime('%Y-%m-%d') if deregistration_date else '',
            'fuel_type': random.choice(fuel_types),
        }
        acquisitions_data.append(acquisition)
    
    return acquisitions_data

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
    # iload_vehicle_dummy_data.csv 에서 vehicle_id 를 읽어와야 하지만, 
    # 여기서는 스크립트 실행 순서를 고려하여 임의의 ID를 사용하거나, 
    # 실제 파일에서 읽어오는 로직을 추가해야 합니다.
    # 현재는 generate_dummy_vehicles 에서 생성된 ID 패턴을 가정합니다.
    vehicle_ids = [f'vehicle_iload_{i+1}' for i in range(20)] 
    acquisitions = generate_dummy_acquisitions(num_records=20, vehicle_ids=vehicle_ids)
    write_to_csv(acquisitions, 'iload_vehicle_acquisition_dummy_data.csv')
