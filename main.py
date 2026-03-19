import os
import json
import re
import time
from playwright.sync_api import sync_playwright
from supabase import create_client

# 설정
url = "https://brand.naver.com/thankstamp/products/5080292253"
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

def scrape_and_save():
    with sync_playwright() as p:
        # 가상 브라우저 실행 (사람처럼 보이기 위한 설정 추가)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        print(f"{url} 접속 중...")
        page.goto(url, wait_until="domcontentloaded")
        
        # 페이지 로딩을 위해 5초간 대기 (필수!)
        time.sleep(5)
        
        # 방식 1: 브라우저 메모리에서 직접 추출
        data = page.evaluate("window.__PRELOADED_STATE__")
        
        # 방식 2: 메모리에 없으면 HTML 소스에서 추출
        if not data:
            html = page.content()
            match = re.search(r'window.__PRELOADED_STATE__\s*=\s*({.*?});', html, re.S)
            if match:
                data = json.loads(match.group(1))

        if not data:
            print("모든 방법으로도 데이터를 찾지 못했습니다.")
            browser.close()
            return

        # 데이터 파싱 시작
        try:
            product_data = data['product']
            product_name = product_data['name']
            base_price = product_data['salePrice']
            
            # 배송비 (경로가 다양할 수 있어 예외처리)
            delivery_fee = 0
            try:
                delivery_fee = product_data['delivery']['bundleGroupDeliveryPolicy']['baseFee']
            except:
                pass

            options = product_data.get('options', [])
            
            for opt in options:
                option_name = opt.get('optionName1', '기본')
                stock = opt.get('stockQuantity', 0)
                total_price = base_price + opt.get('price', 0)
                
                # 중량 추출 및 kg당 가격 계산
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
                print(f"✅ 저장 완료: {option_name} (재고: {stock})")
        
        except Exception as e:
            print(f"데이터 파싱 중 오류 발생: {e}")

        browser.close()

if __name__ == "__main__":
    scrape_and_save()
