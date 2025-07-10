import csv
import random
from faker import Faker

fake = Faker('ko_KR')

def generate_dummy_vehicles(num_records=20):
    vehicles_data = []
    vehicle_types = ['sedan', 'hatchback', 'coupe', 'suv', 'truck', 'trailer', 'motorcycle', 'van', 'ship', 'plane', 'special', 'etc']
    carName = ['BMW', 'K8', 'K7', '마티즈', '아반떼', '스타렉스', '소나타', '산타페', '모하비', '람보르기니', '지바겐']
    
    for i in range(num_records):
        vehicle = {
            'id': f'vehicle_iload_{i+1}', # 외부 ID
            'name': random.choice(carName), # 회사명과 단어를 조합하여 차량 모델명 생성
            'vehicle_type': random.choice(vehicle_types),
            'is_active': random.choice([True, True, True, False]), # 대부분 활성으로
            'description': fake.text(max_nb_chars=100) if random.random() < 0.5 else '', # 50% 확률로 설명 추가
        }
        vehicles_data.append(vehicle)
    
    return vehicles_data

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
    vehicles = generate_dummy_vehicles(num_records=20)
    write_to_csv(vehicles, 'iload_vehicle_dummy_data.csv')