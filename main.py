import os
import requests
import json
import time
import random
from supabase import create_client

# 설정
product_id = "5080292253"
api_url = f"https://smartstore.naver.com/i/v1/contents/pc/products/{product_id}"

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

def scrape_and_save():
    # 429 에러를 피하기 위해 진짜 브라우저처럼 위장 (헤더 강화)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Origin': 'https://brand.naver.com',
        'Referer': f'https://brand.naver.com/thankstamp/products/{product_id}',
        'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
    }

    # 즉시 요청하지 않고 1~3초 사이 랜덤하게 대기 (사람처럼 보이게 함)
    time.sleep(random.uniform(1.0, 3.0))

    print(f"상품 ID {product_id} 데이터 요청 중...")
    
    # 세션을 사용하면 쿠키 등이 유지되어 더 안전합니다
    session = requests.Session()
    response = session.get(api_url, headers=headers)
    
    if response.status_code == 429:
        print("네이버가 일시적으로 차단했습니다(429). 10초 후 재시도합니다...")
        time.sleep(10)
        response = session.get(api_url, headers=headers)

    if response.status_code != 200:
        print(f"데이터를 가져오지 못했습니다. (상태 코드: {response.status_code})")
        return

    data = response.json()
    
    # 데이터 추출 (이전과 동일)
    product_name = data['product']['name']
    base_price = data['product']['salePrice']
    delivery_fee = data['product']['delivery']['bundleGroupDeliveryPolicy']['baseFee']
    
    options = data['product'].get('options', [])
    
    if not options:
        save_to_supabase(product_name, "기본", base_price, data['product']['stockQuantity'], delivery_fee)
    else:
        for opt in options:
            option_name = opt.get('optionName1', '기본')
            stock = opt.get('stockQuantity', 0)
            total_price = base_price + opt.get('price', 0)
            save_to_supabase(product_name, option_name, total_price, stock, delivery_fee)

def save_to_supabase(p_name, o_name, price, stock, delivery):
    import re
    weight_match = re.search(r'(\d+)kg', o_name)
    weight_num = int(weight_match.group(1)) if weight_match else 1
    price_per_kg = price / weight_num

    supabase.table("price_tracker").insert({
        "product_name": p_name,
        "weight_option": o_name,
        "price": price,
        "price_per_kg": round(price_per_kg, 2),
        "stock_quantity": stock,
        "delivery_fee": delivery
    }).execute()
    print(f"✅ 저장 성공: {o_name} (재고: {stock})")

if __name__ == "__main__":
    scrape_and_save()
