import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import os

# 設定要搜尋的關鍵字 (你可以隨時在這裡新增)
# 使用 URL 編碼或是直接用中文，Google News RSS 通常支援
KEYWORDS = [
    "AI Liquid Cooling",
    "AI 水冷",
    "MGCooling",
    "Immersion Cooling", # 浸沒式冷卻
    "Direct-to-Chip Cooling" # 直接晶片冷卻
]

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
        print(f"Error fetching news for {keyword}: {e}")
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
        # RSS 的結構通常是 channel -> item
        for item in root.findall('./channel/item')[:5]: # 每個關鍵字只抓前 5 篇最新的
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text
            
            news_items.append({
                'title': title,
                'link': link,
                'pub_date': pub_date
            })
    except Exception as e:
        print(f"XML Parsing Error: {e}")
        
    return news_items

def generate_markdown_report(all_news):
    """
    將所有新聞彙整成 Markdown 格式的報告
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    content = f"# 🧊 MGCooling AI 水冷每日情報 - {today}\n\n"
    content += "本報告由 GitHub Actions 自動生成，彙整網路上最新的產業動態。\n\n"
    
    if not all_news:
        content += "⚠️ 今日搜尋無重大更新，或連線發生異常。\n"
    
    for keyword, items in all_news.items():
        content += f"## 🔍 關鍵字：{keyword}\n"
        if not items:
            content += "* 尚無最新相關新聞。\n"
        for item in items:
            # 簡單清理標題中的網站名稱 (通常格式為 Title - Source)
            clean_title = item['title'].split(' - ')[0]
            content += f"- **[{clean_title}]({item['link']})**\n"
            content += f"  - <small>發布時間: {item['pub_date']}</small>\n"
        content += "\n"
        
    content += "---\n"
    content += f"*Report generated at {datetime.now().strftime('%H:%M:%S UTC')}*\n"
    
    return content

def main():
    print("開始執行每日新聞搜集...")
    all_news_data = {}
    
    for kw in KEYWORDS:
        print(f"正在搜尋: {kw} ...")
        xml_data = fetch_google_news_rss(kw)
        items = parse_news(xml_data)
        all_news_data[kw] = items
        
    report_content = generate_markdown_report(all_news_data)
    
    # 將結果寫入 README.md (這樣你打開 GitHub 首頁就能看到)
    # 也可以改為寫入 daily_reports/date.md
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print("報告已更新至 README.md")

if __name__ == "__main__":
    main()
