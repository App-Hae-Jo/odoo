
import csv
import random
from faker import Faker

fake = Faker('ko_KR') # 한국어 데이터 생성을 위해 ko_KR 로케일 사용

def generate_dummy_partners(num_records=20):
    partners_data = []
    
    # Odoo의 res.country 및 res.currency에 존재하는 값이라고 가정
    # 실제 Odoo 인스턴스에 맞게 조정 필요
    country_codes = ['KR', 'US', 'JP', 'CN', 'DE', 'FR']
    currency_codes = ['KRW', 'USD', 'EUR', 'JPY']

    for i in range(num_records):
        is_iload_customer = random.choice([True, False])
        
        partner = {
            'id': f'partner_iload_{i+1}', # 외부 ID
            'name': fake.company(),
            'is_company': True,
            'email': fake.company_email(),
            'phone': fake.phone_number(),
            'street': fake.street_address(),
            'city': fake.city(),
            'zip': fake.postcode(),
            'country_id/code': random.choice(country_codes), # Many2one 필드는 외부 ID로 참조
            'is_iload_customer': is_iload_customer,
            'iload_customer_code': f'CUST{random.randint(10000, 99999)}' if is_iload_customer else '',
            'customs_clearance_no': fake.ssn() if is_iload_customer else '', # 개인통관고유부호는 주민등록번호 형식으로 임시 생성
            'currency_id/name': random.choice(currency_codes), # Many2one 필드는 외부 ID로 참조
            'destination_country_id/code': random.choice(country_codes), # Many2one 필드는 외부 ID로 참조
        }
        partners_data.append(partner)
    
    return partners_data

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
    partners = generate_dummy_partners(num_records=20)
    write_to_csv(partners, 'iload_res_partner_dummy_data.csv')
