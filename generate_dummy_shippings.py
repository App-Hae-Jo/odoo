
import csv
import random
from faker import Faker
from datetime import date, timedelta

fake = Faker('ko_KR')

def generate_dummy_shippings(num_records=30, order_detail_ids=None):
    shippings_data = []
    
    if order_detail_ids is None:
        order_detail_ids = [f'order_detail_iload_{i+1}' for i in range(40)] # 기본값으로 40개 가정

    shipping_methods = ['container', 'ro_ro']

    for i in range(num_records):
        shipping_date = fake.date_between(start_date='-6M', end_date='today')
        
        shipping = {
            'id': f'shipping_iload_{i+1}', # 외부 ID
            'name': f'SHIP{random.randint(100000, 999999)}', # 임의의 선적 번호
            'order_detail_id/id': random.choice(order_detail_ids), # iload.order.detail 참조
            'shipping_method': random.choice(shipping_methods),
            'shipping_date': shipping_date.strftime('%Y-%m-%d'),
        }
        shippings_data.append(shipping)
    
    return shippings_data

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
    # iload_order_detail_dummy_data.csv 에서 order_detail_id 를 읽어와야 하지만, 
    # 여기서는 스크립트 실행 순서를 고려하여 임의의 ID를 가정합니다.
    order_detail_ids = [f'order_detail_iload_{i+1}' for i in range(40)] 
    shippings = generate_dummy_shippings(num_records=30, order_detail_ids=order_detail_ids)
    write_to_csv(shippings, 'iload_shipping_dummy_data.csv')
