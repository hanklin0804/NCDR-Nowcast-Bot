#!/usr/bin/env python3
"""雷達圖像 LINE Bot 主程式"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from src.image_processor import process_radar_images

try:
    from linebot import LineBotApi, WebhookHandler
    from linebot.models import TextSendMessage, ImageSendMessage
    import requests
except ImportError as e:
    print(f"❌ 缺少必要套件: {e}")
    print("請安裝: pip install -r requirements.txt")
    sys.exit(1)

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_USER_ID = os.getenv('LINE_USER_ID')

if not all([LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, LINE_USER_ID]):
    print("❌ 環境變數未設定完整")
    print("需要: LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, LINE_USER_ID")
    sys.exit(1)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def fetch_radar_data():
    """取得雷達資料"""
    try:
        print("📡 取得雷達資料...")
        api_url = "https://watch.ncdr.nat.gov.tw/wh/cv_ncdrnowcast_info"
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        lines = response.text.strip().split('\n')
        radar_data = []
        
        for i, line in enumerate(lines[1:], 1):
            if line.strip():
                parts = line.strip().split(',')
                if len(parts) >= 5:
                    radar_data.append({
                        'id': i,
                        'timestamp': parts[1],
                        'file': parts[2],
                        'size': parts[3],
                        'file_size': parts[4]
                    })
        
        print(f"✅ 成功取得 {len(radar_data)} 筆雷達資料")
        return radar_data
        
    except Exception as e:
        print(f"❌ 取得雷達資料失敗: {e}")
        return []

def send_radar_notification(image_url):
    """發送雷達圖像通知"""
    try:
        if not image_url:
            message = "❌ 雷達圖像處理失敗"
            line_bot_api.push_message(
                LINE_USER_ID,
                TextSendMessage(text=message)
            )
            return False
        
        timestamp = datetime.now().strftime("%Y/%m/%d %H:%M")
        message = f"🌧️ 雷達回波動畫 ({timestamp})"
        
        line_bot_api.push_message(
            LINE_USER_ID,
            [
                TextSendMessage(text=message),
                ImageSendMessage(
                    original_content_url=image_url,
                    preview_image_url=image_url
                )
            ]
        )
        
        print("✅ LINE 通知已發送")
        return True
        
    except Exception as e:
        print(f"❌ 發送 LINE 通知失敗: {e}")
        return False

def main():
    """主程式"""
    print("🚀 開始雷達圖像 LINE Bot...")
    print(f"⏰ 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 取得雷達資料
    radar_data = fetch_radar_data()
    if not radar_data:
        print("❌ 沒有雷達資料，程式結束")
        sys.exit(1)
    
    # 2. 處理圖像
    result = process_radar_images(radar_data)
    if not result:
        print("❌ 圖像處理失敗，程式結束")
        sys.exit(1)
    
    # 3. 發送通知
    success = send_radar_notification(result.get('image_url'))
    
    if success:
        print("🎉 雷達圖像 LINE Bot 執行完成")
        print(f"📊 處理統計:")
        print(f"   下載圖片: {result.get('downloaded_count', 0)} 張")
        print(f"   動畫路徑: {result.get('gif_path', 'N/A')}")
        print(f"   雲端連結: {result.get('image_url', 'N/A')}")
    else:
        print("❌ 程式執行失敗")
        sys.exit(1)

if __name__ == "__main__":
    main()