import os
import requests
import json
from supabase import create_client

# 설정
product_id = "5080292253"
# 네이버 스마트스토어 상품 상세 API 주소
api_url = f"https://smartstore.naver.com/i/v1/contents/pc/products/{product_id}"

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

def scrape_and_save():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': f'https://brand.naver.com/thankstamp/products/{product_id}'
    }

    print(f"상품 ID {product_id} 데이터 요청 중...")
    response = requests.get(api_url, headers=headers)
    
    if response.status_code != 200:
        print(f"데이터를 가져오지 못했습니다. (상태 코드: {response.status_code})")
        return

    data = response.json()
    
    # 필요한 정보 추출
    product_name = data['product']['name']
    base_price = data['product']['salePrice']
    delivery_fee = data['product']['delivery']['bundleGroupDeliveryPolicy']['baseFee']
    
    # 옵션 정보 (재고 포함)
    options = data['product'].get('options', [])
    
    if not options:
        # 옵션이 없는 단일 상품인 경우
        save_to_supabase(product_name, "기본", base_price, data['product']['stockQuantity'], delivery_fee)
    else:
        for opt in options:
            option_name = opt.get('optionName1', '기본')
            stock = opt.get('stockQuantity', 0)
            total_price = base_price + opt.get('price', 0)
            save_to_supabase(product_name, option_name, total_price, stock, delivery_fee)

def save_to_supabase(p_name, o_name, price, stock, delivery):
    # kg당 가격 계산 로직
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
