import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import os

def load_keywords():
    """
    讀取 keywords.txt，如果檔案不存在則使用預設值
    """
    default_keywords = ["AI Liquid Cooling", "AI 水冷", "MGCooling"]
    
    if not os.path.exists("keywords.txt"):
        print("⚠️ 找不到 keywords.txt，將使用預設關鍵字。")
        return default_keywords

    with open("keywords.txt", "r", encoding="utf-8") as f:
        # 讀取每一行，去除空白，並過濾掉空行
        keywords = [line.strip() for line in f if line.strip()]
    
    print(f"✅ 已載入 {len(keywords)} 個關鍵字")
    return keywords

def fetch_google_news_rss(keyword):
    """
    透過 Google News RSS 取得特定關鍵字的新聞
    """
    base_url = "https://news.google.com/rss/search"
    # 設定參數：q=關鍵字, hl=語言(繁體中文), gl=地區(台灣), ceid=地區設定
    params = {
        "q": keyword,
        "hl": "zh-TW",
        "gl": "TW",
        "ceid": "TW:zh-Hant"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"❌ Error fetching news for {keyword}: {e}")
        return None

def parse_news(xml_content):
    """
    解析 XML 格式的新聞資料
    """
    if not xml_content:
        return []
        
    news_items = []
    try:
        root = ET.fromstring(xml_content)
        # 每個關鍵字只抓前 5 篇
        for item in root.findall('./channel/item')[:5]: 
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text
            
            # --- 🛠️ 標題清洗區 ---
            # 1. 去除標題後面的媒體名稱 (例如 " - 數位時代")
            clean_title = title.split(' - ')[0]
            # 2. 【關鍵修正】把半形 '|' 換成全形 '｜'，避免 GitHub 把標題誤判成表格
            clean_title = clean_title.replace('|', '｜')
            # 3. 去除可能導致換行的符號
            clean_title = clean_title.replace('\n', ' ')
            
            news_items.append({
                'title': clean_title,
                'link': link,
                'pub_date': pub_date
            })
    except Exception as e:
        print(f"⚠️ XML Parsing Error: {e}")
        
    return news_items

def generate_markdown_report(all_news):
    """
    將所有新聞彙整成 Markdown 格式的報告，包含重點摘要
    """
    # 設定台灣時間 (UTC+8)
    tw_tz = timezone(timedelta(hours=8))
    today = datetime.now(tw_tz).strftime("%Y-%m-%d")
    
    content = f"# 🧊 MGCooling AI 水冷每日情報 - {today}\n\n"
    
    # --- 🔘 新增：手動更新按鈕 ---
    # 這個連結會帶使用者到 GitHub Actions 的執行頁面
    # 為了方便，這裡直接填入你的專案路徑
    repo_actions_url = "https://github.com/odinchen2025/mgcooling-news-bot/actions/workflows/daily_scan.yml"
    content += f"[![手動更新](https://img.shields.io/badge/按此手動更新-Run%20Update-2ea44f?style=for-the-badge&logo=github)]({repo_actions_url})\n\n"
    
    content += "本報告由 GitHub Actions 自動生成，彙整網路上最新的產業動態。\n\n"
    
    # --- 🔥 重點摘要區塊 (Top Highlights) ---
    content += "## 🔥 本日焦點 (Top Highlights)\n"
    content += "> 快速瀏覽各關鍵字的頭條新聞：\n\n"
    
    has_highlights = False
    highlight_count = 0
    
    # 邏輯：從每個關鍵字類別中，挑選「第一則」新聞作為重點，最多挑 5 則
    for keyword, items in all_news.items():
        if items and highlight_count < 5:
            top_item = items[0] # 取該類別的第一篇
            # 格式：1. [關鍵字] 新聞標題
            content += f"1. **[{keyword}]** [{top_item['title']}]({top_item['link']})\n"
            highlight_count += 1
            has_highlights = True
            
    if not has_highlights:
        content += "* 今日無重大新聞更新。\n"
    
    content += "\n---\n\n"
    
    # --- 📋 詳細清單區塊 ---
    content += "## 📋 詳細新聞列表\n"
    
    if not all_news:
        content += "⚠️ 今日搜尋無重大更新，或連線發生異常。\n"
    
    for keyword, items in all_news.items():
        content += f"### 🔍 {keyword}\n"
        if not items:
            content += "* 尚無最新相關新聞。\n"
        for item in items:
            content += f"- [{item['title']}]({item['link']})\n"
        content += "\n"
        
    content += "---\n"
    content += f"*Report generated at {datetime.now(tw_tz).strftime('%Y-%m-%d %H:%M:%S (Taipei Time)')}*\n"
    
    return content

def main():
    print("🚀 開始執行每日新聞搜集...")
    
    # 1. 讀取關鍵字
    keywords = load_keywords()
    
    all_news_data = {}
    
    # 2. 爬取新聞
    for kw in keywords:
        print(f"📡 正在搜尋: {kw} ...")
        xml_data = fetch_google_news_rss(kw)
        items = parse_news(xml_data)
        all_news_data[kw] = items
        
    # 3. 生成報告
    print("📝 正在撰寫報告...")
    report_content = generate_markdown_report(all_news_data)
    
    # 4. 將結果寫入 README.md
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print("✅ 報告已更新至 README.md")

if __name__ == "__main__":
    main()
