import requests
from bs4 import BeautifulSoup
import os
import time
import json
import re

def fetch_youtube_trending_videos():
    url = "https://www.youtube.com/feed/trending"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"請求失敗: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 嘗試從所有 script 標籤中提取 JSON 數據
    script_tags = soup.find_all("script")
    
    data = None
    for script in script_tags:
        script_content = script.string
        if script_content:
            # 嘗試不同的模式來匹配 JSON 數據
            patterns = [
                r'var ytInitialData = (.+?);</script>',
                r'ytInitialData = (.+?);',
                r'window\["ytInitialData"\] = (.+?);'
            ]
            for pattern in patterns:
                match = re.search(pattern, script_content, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group(1))
                        print("成功提取 JSON 數據")
                        break
                    except json.JSONDecodeError:
                        print(f"JSON 解析錯誤，嘗試下一個模式")
                        continue
            if data:
                break
    
    if not data:
        print("無法從任何 script 標籤中提取有效的 JSON 數據")
        print("頁面內容摘要:")
        print(soup.get_text()[:500])  # 打印頁面文本的前500個字符
        return

    # 提取視頻信息
    videos = []
    try:
        contents = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents']
        for content in contents:
            if 'itemSectionRenderer' in content:
                items = content['itemSectionRenderer']['contents']
                for item in items:
                    if 'shelfRenderer' in item:
                        videos.extend(item['shelfRenderer']['content']['expandedShelfContentsRenderer']['items'])
                        break
                if videos:
                    break
    except KeyError:
        print("無法從 JSON 數據中提取視頻信息")
        print("JSON 數據結構:")
        print(json.dumps(data, indent=2)[:1000])  # 打印 JSON 數據的前1000個字符
        return

    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    file_path = os.path.join(desktop_path, "YouTube-output.txt")
    
    with open(file_path, "a", encoding="utf-8") as file:
        file.write(f"\n--- 抓取時間: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n\n")
        
        for video in videos[:10]:
            video_data = video.get('videoRenderer', {})
            title = video_data.get('title', {}).get('runs', [{}])[0].get('text', 'No title')
            video_id = video_data.get('videoId', '')
            link = f"https://www.youtube.com/watch?v={video_id}" if video_id else 'No link'
            description = video_data.get('descriptionSnippet', {}).get('runs', [{}])[0].get('text', 'No description')
            
            file.write(f"標題: {title}\n")
            file.write(f"鏈接: {link}\n")
            file.write(f"簡介: {description}\n")
            file.write("----------------------------------\n")
    
    print(f"熱門視頻已追加到 {file_path}")

fetch_youtube_trending_videos()
