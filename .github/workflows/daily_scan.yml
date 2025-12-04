name: Daily AI Cooling News Scan

# 設定觸發條件
on:
  schedule:
    # 修改為 UTC 23:00 (即台灣時間隔天早上 07:00)
    - cron: '0 23 * * *'
  # 允許手動點擊按鈕執行 (方便測試)
  workflow_dispatch:

# 設定權限，允許寫入儲存庫
permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - name: 下載程式碼 (Checkout code)
      uses: actions/checkout@v3

    - name: 設定 Python 環境
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: 安裝必要套件
      run: |
        pip install -r requirements.txt

    - name: 執行爬蟲程式
      run: |
        python daily_bot.py

    - name: 提交並更新報告 (Commit & Push)
      run: |
        git config --global user.name "MGCooling-Bot"
        git config --global user.email "bot@mgcooling.com"
        git add README.md
        # 如果有變更才提交，避免錯誤
        git commit -m "Auto-update: Daily AI Cooling News" || exit 0
        git push
