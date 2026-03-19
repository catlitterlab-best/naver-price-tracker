name: Naver Price Tracker
on:
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch: 

jobs:
  run_scraper:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium --with-deps
      - name: Run Script
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: python main.py
