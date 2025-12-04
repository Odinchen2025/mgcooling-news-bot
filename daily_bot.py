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
        # RSS 的結構通常是 channel -> item
        # 每個關鍵字只抓前 5 篇最新的
        for item in root.findall('./channel/item')[:5]: 
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text
            
            # 簡單清理標題 (去除媒體名稱，通常格式為 Title - Source)
            clean_title = title.split(' - ')[0]
            
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
    content += "本報告由 GitHub Actions 自動生成，彙整網路上最新的產業動態。\n\n"
    
    # --- 🔥 新增功能：生成重點摘要 (Top Highlights) ---
    content += "## 🔥 本日焦點 (Top Highlights)\n"
    content += "> 從各個關鍵字中精選出的頭條新聞：\n\n"
    
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
    
    # --- 📋 生成詳細清單 ---
    content += "## 📋 詳細新聞列表\n"
    
    if not all_news:
        content += "⚠️ 今日搜尋無重大更新，或連線發生異常。\n"
    
    for keyword, items in all_news.items():
        content += f"### 🔍 {keyword}\n"
        if not items:
            content += "* 尚無最新相關新聞。\n"
        for item in items:
            content += f"- [{item['title']}]({item['link']})\n"
            # 若不想顯示日期可註解掉下面這行
            # content += f"  - <small>{item['pub_date']}</small>\n"
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
