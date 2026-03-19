import os
import json
import re
import requests
from bs4 import BeautifulSoup
from supabase import create_client

# 설정
url = "https://brand.naver.com/thankstamp/products/5080292253"
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

def scrape_and_save():
    # 실제 브라우저처럼 보이기 위한 헤더 설정
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://search.shopping.naver.com/'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 데이터가 포함된 스크립트 찾기 (방식 개선)
    scripts = soup.find_all('script')
    target_script = None
    for s in scripts:
        if s.string and 'window.__PRELOADED_STATE__' in s.string:
            target_script = s.string
            break
            
    if not target_script:
        print("데이터를 찾지 못했습니다. 네이버가 접근을 차단했을 수 있습니다.")
        return

    # JSON 데이터 추출
    json_text = re.search(r'window.__PRELOADED_STATE__\s*=\s*({.*?});', target_script, re.S).group(1)
    data = json.loads(json_text)
    
    product_data = data['product']
    product_name = product_data['name']
    base_price = product_data['salePrice']
    
    # 배송비 추출 (구조 대응)
    try:
        delivery_fee = product_data['delivery']['bundleGroupDeliveryPolicy']['baseFee']
    except:
        delivery_fee = 0

    options = product_data.get('options', [])
    
    for opt in options:
        option_name = opt.get('optionName1', '기본')
        stock = opt.get('stockQuantity', 0)
        total_price = base_price + opt.get('price', 0)
        
        # kg당 가격 계산
        weight_match = re.search(r'(\d+)kg', option_name)
        weight_num = int(weight_match.group(1)) if weight_match else 1
        price_per_kg = total_price / weight_num
        
        # Supabase 저장
        supabase.table("price_tracker").insert({
            "product_name": product_name,
            "weight_option": option_name,
            "price": total_price,
            "price_per_kg": round(price_per_kg, 2),
            "stock_quantity": stock,
            "delivery_fee": delivery_fee
        }).execute()
        print(f"저장 완료: {option_name} - 재고 {stock}")

if __name__ == "__main__":
    scrape_and_save()
