import os
import json
import re
import requests
from bs4 import BeautifulSoup
from supabase import create_client

# 1. 설정 (GitHub Secrets에서 불러올 예정)
url = "https://brand.naver.com/thankstamp/products/5080292253"
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

def scrape_and_save():
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 페이지 내 데이터 덩어리(PRELOADED_STATE) 찾기
    script_tag = soup.find('script', text=re.compile('window.__PRELOADED_STATE__'))
    json_text = re.search(r'window.__PRELOADED_STATE__\s*=\s*({.*?});', script_tag.string, re.S).group(1)
    data = json.loads(json_text)
    
    product_name = data['product']['name']
    base_price = data['product']['salePrice']
    delivery_fee = data['product']['delivery']['bundleGroupDeliveryPolicy']['baseFee']
    options = data['product']['options']

    for opt in options:
        option_name = opt['optionName1'] # 예: "6kg"
        stock = opt['stockQuantity']    # 숨겨진 재고
        total_price = base_price + opt.get('price', 0)
        
        # kg당 가격 계산 (숫자만 추출)
        weight_num = re.findall(r'\d+', option_name)
        price_per_kg = total_price / int(weight_num[0]) if weight_num else 0
        
        # Supabase에 한 줄 저장
        supabase.table("price_tracker").insert({
            "product_name": product_name,
            "weight_option": option_name,
            "price": total_price,
            "price_per_kg": round(price_per_kg, 2),
            "stock_quantity": stock,
            "delivery_fee": delivery_fee
        }).execute()

if __name__ == "__main__":
    scrape_and_save()
