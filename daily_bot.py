import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import os
import json
import re
from email.utils import parsedate_to_datetime

def load_keywords():
    """ 讀取 keywords.txt """
    default_keywords = ["MGCooling", "AI Liquid Cooling", "AI 水冷"]
    if not os.path.exists("keywords.txt"):
        print("⚠️ 找不到 keywords.txt，將使用預設關鍵字。")
        return default_keywords
    with open("keywords.txt", "r", encoding="utf-8") as f:
        keywords = [line.strip() for line in f if line.strip()]
    print(f"✅ 已載入 {len(keywords)} 個關鍵字")
    return keywords

def fetch_google_news_rss(keyword):
    """ 透過 Google News RSS 取得特定關鍵字的新聞 """
    base_url = "https://news.google.com/rss/search"
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

def clean_html_tags(text):
    """ 清除摘要中的 HTML 標籤 """
    if not text: return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def parse_news(xml_content):
    """ 解析 XML 格式的新聞資料 """
    if not xml_content:
        return []
    news_items = []
    try:
        root = ET.fromstring(xml_content)
        # 抓取前 5 篇作為緩衝
        for item in root.findall('./channel/item')[:5]: 
            title = item.find('title').text
            link = item.find('link').text
            pub_date_raw = item.find('pubDate').text
            
            # --- 🛠️ 日期格式化 (M/D/YY) ---
            try:
                # 使用 email.utils 解析 RFC 822 格式
                dt_obj = parsedate_to_datetime(pub_date_raw)
                # 轉成 M/D/YY 字串 (例如 4/26/25)
                pub_date = f"{dt_obj.month}/{dt_obj.day}/{dt_obj.strftime('%y')}"
            except Exception as e:
                # 如果解析失敗，維持原樣
                pub_date = pub_date_raw
            
            description_node = item.find('description')
            raw_desc = description_node.text if description_node is not None else ""
            clean_desc = clean_html_tags(raw_desc)
            
            clean_title = title.split(' - ')[0]
            clean_title = clean_title.replace('|', '｜').replace('\n', ' ')
            
            news_items.append({
                'title': clean_title,
                'link': link,
                'pub_date': pub_date,
                'description': clean_desc
            })
    except Exception as e:
        print(f"⚠️ XML Parsing Error: {e}")
    return news_items

def generate_markdown_report(all_news):
    """ 將所有新聞彙整成 Markdown 格式的報告 """
    tw_tz = timezone(timedelta(hours=8))
    
    # 取得現在時間
    now = datetime.now(tw_tz)
    # 標題日期格式 M/D/YY
    today = f"{now.month}/{now.day}/{now.strftime('%y')}"
    # 詳細更新時間 YYYY/MM/DD HH:MM
    update_time_str = now.strftime('%Y/%m/%d %H:%M')
    
    content = f"# 🧊 MGCooling AI 水冷每日情報 - {today}\n\n"
    
    repo_actions_url = "https://github.com/odinchen2025/mgcooling-news-bot/actions/workflows/daily_scan.yml"
    
    # 更新按鈕
    content += f"[![手動更新](https://img.shields.io/badge/按此手動更新-Run_Update-2ea44f?style=for-the-badge&logo=github)]({repo_actions_url})\n"
    
    # --- 🕒 新增：淡淡灰白色更新時間 (靠右對齊) ---
    content += f"<p align='right' style='color: #bfbfbf; font-size: 13px; margin-top: -20px;'>更新時間：{update_time_str}</p>\n\n"
    
    # --- 🔥 生成重點摘要 ---
    content += "## 🔥 本日焦點 (Top Highlights)\n"
    content += "> 快速瀏覽產業頭條：\n\n"
    
    priority_highlights = []
    general_highlights = []
    processed_keys = set()
    
    # 優先篩選
    for keyword, items in all_news.items():
        if items:
            if "MGCooling" in keyword or "元鈦" in keyword:
                top_item = items[0]
                priority_highlights.append(f"1. **[{keyword}]** [{top_item['title']}]({top_item['link']}) <small>({top_item['pub_date']})</small>")
                processed_keys.add(keyword)

    # 一般篩選
    max_general_count = 5
    current_general_count = 0
    for keyword, items in all_news.items():
        if keyword in processed_keys: continue
        if items and current_general_count < max_general_count:
            top_item = items[0]
            general_highlights.append(f"1. **[{keyword}]** [{top_item['title']}]({top_item['link']}) <small>({top_item['pub_date']})</small>")
            current_general_count += 1
            
    final_highlights = priority_highlights + general_highlights
    if final_highlights:
        for line in final_highlights: content += line + "\n"
    else:
        content += "* 今日無重大新聞更新。\n"
    
    content += "\n---\n\n"
    
    # --- 📋 生成詳細清單 (依據最新到最舊) ---
    content += "## 📋 詳細新聞列表\n"
    
    for keyword, items in all_news.items():
        content += f"### 🔍 {keyword}\n"
        if not items:
            content += "* 尚無最新相關新聞。\n"
        
        # 只顯示前 3 則
        for item in items[:3]:
            # 日期在標題最前面，淺灰色，格式 M/D/YY
            content += f"- <small style='color:gray;'>{item['pub_date']}</small> [{item['title']}]({item['link']})\n"
        content += "\n"
    
    content += "---\n"
    content += f"*Report generated at {datetime.now(tw_tz).strftime('%Y-%m-%d %H:%M:%S (Taipei Time)')}*\n"
    return content

def main():
    print("🚀 開始執行每日新聞搜集...")
    keywords = load_keywords()
    all_news_data = {}
    
    # 1. 爬取新聞
    for kw in keywords:
        print(f"📡 正在搜尋: {kw} ...")
        xml_data = fetch_google_news_rss(kw)
        items = parse_news(xml_data)
        all_news_data[kw] = items
        
    # 2. 生成 Markdown 報告
    print("📝 正在撰寫 Markdown 報告...")
    report_content = generate_markdown_report(all_news_data)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(report_content)
        
    # 3. 輸出 JSON 資料
    print("💾 正在輸出 JSON 資料...")
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(all_news_data, f, ensure_ascii=False, indent=4)

    print("✅ 報告與資料已更新 (README.md & news.json)")

if __name__ == "__main__":
    main()
