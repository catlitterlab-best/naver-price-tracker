import os
import json
import re
import asyncio
from playwright.sync_api import sync_playwright
from supabase import create_client

# 설정
url = "https://brand.naver.com/thankstamp/products/5080292253"
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

def scrape_and_save():
    with sync_playwright() as p:
        # 가상 브라우저 실행
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print("페이지 접속 중...")
        page.goto(url, wait_until="networkidle")
        
        # 브라우저 내부에서 window.__PRELOADED_STATE__ 변수 직접 가져오기
        data = page.evaluate("window.__PRELOADED_STATE__")
        
        if not data:
            print("데이터를 찾지 못했습니다.")
            browser.close()
            return

        product_data = data['product']
        product_name = product_data['name']
        base_price = product_data['salePrice']
        
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

        browser.close()

if __name__ == "__main__":
    scrape_and_save()
