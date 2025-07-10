
import csv
import random
from faker import Faker
from datetime import date, timedelta

fake = Faker('ko_KR')

def generate_dummy_orders(num_records=20, partner_ids=None):
    orders_data = []
    
    if partner_ids is None:
        partner_ids = [f'partner_iload_{i+1}' for i in range(20)] # 기본값으로 20개 가정

    country_codes = ['KR', 'US', 'JP', 'CN', 'DE', 'FR']

    for i in range(num_records):
        order_date = fake.date_between(start_date='-1y', end_date='today')
        
        # 고객사, 수취인, 담당자는 기존 파트너 ID 내에서 선택
        customer_partner_id = random.choice(partner_ids)
        receiver_partner_id = random.choice(partner_ids)
        contact_person_id = random.choice(partner_ids)

        order = {
            'id': f'order_iload_{i+1}', # 외부 ID
            'order_date': order_date.strftime('%Y-%m-%d'),
            'partner_id/id': customer_partner_id, # res.partner 참조
            'receiver_partner_id/id': receiver_partner_id, # res.partner 참조
            'contact_person_id/id': contact_person_id, # res.partner 참조
            'origin_address': fake.address(),
            'origin_country_id/code': random.choice(country_codes), # res.country 참조
            'destination_address': fake.address(),
            'destination_country_id/code': random.choice(country_codes), # res.country 참조
        }
        orders_data.append(order)
    
    return orders_data

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
    # iload_res_partner_dummy_data.csv 에서 partner_id 를 읽어와야 하지만, 
    # 여기서는 스크립트 실행 순서를 고려하여 임의의 ID를 사용하거나, 
    # 실제 파일에서 읽어오는 로직을 추가해야 합니다.
    partner_ids = [f'partner_iload_{i+1}' for i in range(20)] 
    orders = generate_dummy_orders(num_records=20, partner_ids=partner_ids)
    write_to_csv(orders, 'iload_order_dummy_data.csv')
