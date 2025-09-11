#!/usr/bin/env python3
"""發送氣象雷達 LINE 通知"""

import os
import sys
import json
import mimetypes
from datetime import datetime
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    from linebot import LineBotApi
    from linebot.models import TextMessage, ImageMessage, ImageSendMessage
    from linebot.exceptions import LineBotApiError
except ImportError as e:
    print(f"❌ 缺少必要套件: {e}")
    print("請安裝: pip install line-bot-sdk python-dotenv")
    sys.exit(1)

def send_text_notification(message_text):
    """發送文字通知"""
    
    load_dotenv()
    
    channel_access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
    user_id = os.environ.get('LINE_USER_ID')
    
    if not channel_access_token or not user_id:
        print("❌ 請設定 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_USER_ID")
        return False
    
    try:
        line_bot_api = LineBotApi(channel_access_token)
        text_msg = TextMessage(text=message_text)
        line_bot_api.push_message(user_id, text_msg)
        
        print("✅ 文字訊息發送成功")
        return True
        
    except LineBotApiError as e:
        print(f"❌ LINE API 錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 發送失敗: {e}")
        return False

def create_radar_message():
    """建立雷達通知訊息文字"""
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    message = f"""🌧️ 氣象雷達更新 - {current_time}

📍 涵蓋範圍: 台灣全域
⏰ 預測時間: 未來 2 小時  
🔄 更新頻率: 每 10 分鐘

📊 資料來源: 國家災害防救科技中心 (NCDR)
🎬 動畫包含觀測圖與預測圖

⚠️ 注意: 如有強降雨預報，請注意安全！"""

    return message

def upload_image_to_imgur(image_path, client_id=None):
    """上傳圖片到 Imgur (需要 Client ID)"""
    
    if not client_id:
        print("⚠️ 需要 Imgur Client ID 才能上傳圖片")
        return None
    
    try:
        import requests
        import base64
        
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        headers = {'Authorization': f'Client-ID {client_id}'}
        data = {'image': image_data}
        
        response = requests.post('https://api.imgur.com/3/image', 
                               headers=headers, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                return result['data']['link']
        
        print(f"❌ Imgur 上傳失敗: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"❌ 圖片上傳錯誤: {e}")
        return None

def send_image_notification(image_path, preview_image_path=None):
    """發送圖片通知 (自動上傳到免費服務)"""
    
    if not os.path.exists(image_path):
        print(f"❌ 找不到圖片檔案: {image_path}")
        return False
    
    print(f"🌅 嘗試上傳圖片: {image_path}")
    
    # 嘗試多個免費圖片上傳服務
    upload_services = [
        ("catbox.moe", upload_to_catbox),
        ("tmpfiles.org", simple_upload_to_tmpfiles)
    ]
    
    for service_name, upload_func in upload_services:
        print(f"🔄 嘗試 {service_name}...")
        image_url = upload_func(image_path)
        
        if image_url:
            print(f"✅ 上傳成功到 {service_name}")
            return send_image_with_url(image_url, image_url)
        else:
            print(f"❌ {service_name} 上傳失敗")
    
    print("❌ 所有圖片上傳服務都失敗")
    return False

def simple_upload_to_tmpfiles(image_path):
    """上傳圖片到 tmpfiles.org (臨時檔案服務)"""
    try:
        import requests
        
        print(f"📤 上傳到 tmpfiles.org: {os.path.basename(image_path)}")
        
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post('https://tmpfiles.org/api/v1/upload', files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                # tmpfiles.org 會回傳下載連結
                url = result['data']['url']
                # 將 tmpfiles.org 轉換成直接連結
                direct_url = url.replace('tmpfiles.org/', 'tmpfiles.org/dl/')
                print(f"✅ 上傳成功: {direct_url}")
                return direct_url
                
    except Exception as e:
        print(f"❌ tmpfiles.org 上傳失敗: {e}")
    
    return None

def upload_to_catbox(image_path):
    """上傳圖片到 catbox.moe"""
    try:
        import requests
        
        print(f"📤 上傳到 catbox.moe: {os.path.basename(image_path)}")
        
        with open(image_path, 'rb') as f:
            files = {'fileToUpload': f}
            data = {'reqtype': 'fileupload'}
            response = requests.post('https://catbox.moe/user/api.php', files=files, data=data, timeout=30)
        
        if response.status_code == 200 and response.text.startswith('https://'):
            url = response.text.strip()
            print(f"✅ 上傳成功: {url}")
            return url
                
    except Exception as e:
        print(f"❌ catbox.moe 上傳失敗: {e}")
    
    return None

def send_image_with_url(original_content_url, preview_image_url=None):
    """使用 URL 發送圖片"""
    
    load_dotenv()
    
    channel_access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
    user_id = os.environ.get('LINE_USER_ID')
    
    if not channel_access_token or not user_id:
        print("❌ 請設定 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_USER_ID")
        return False
    
    try:
        line_bot_api = LineBotApi(channel_access_token)
        
        # LINE 圖片訊息需要 HTTPS URL
        if not original_content_url.startswith('https://'):
            print("❌ LINE 需要 HTTPS 圖片 URL")
            return False
        
        # 使用相同 URL 作為預覽圖（如果沒有指定）
        if not preview_image_url:
            preview_image_url = original_content_url
        
        image_message = ImageSendMessage(
            original_content_url=original_content_url,
            preview_image_url=preview_image_url
        )
        
        line_bot_api.push_message(user_id, image_message)
        
        print(f"✅ 圖片訊息發送成功: {original_content_url}")
        return True
        
    except LineBotApiError as e:
        print(f"❌ LINE API 錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 發送失敗: {e}")
        return False

def send_radar_animation(gif_path=None, send_image=True):
    """發送雷達動畫通知"""
    
    print("📱 準備發送 LINE 通知...")
    
    # 1. 發送文字訊息
    message_text = create_radar_message()
    text_success = send_text_notification(message_text)
    
    if not text_success:
        print("❌ 文字訊息發送失敗")
        return False
    
    # 2. 嘗試發送圖片（如果有提供路徑且啟用）
    image_success = True
    if send_image and gif_path and os.path.exists(gif_path):
        print(f"🖼️ 嘗試發送圖片: {gif_path}")
        image_success = send_image_notification(gif_path)
        
        if not image_success:
            print("⚠️ 圖片發送失敗，但文字訊息已發送")
    
    return text_success

def load_animation_info():
    """載入動畫資訊"""
    try:
        with open('animation_info.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ 找不到動畫資訊檔案")
        return None
    except Exception as e:
        print(f"⚠️ 讀取動畫資訊失敗: {e}")
        return None

def test_notification():
    """測試通知功能"""
    print("🧪 測試 LINE 通知功能...")
    
    test_message = f"""🧪 測試訊息 - {datetime.now().strftime('%H:%M:%S')}

這是氣象雷達機器人的測試通知。

如果你收到這個訊息，表示：
✅ LINE Bot 設定正確
✅ 通知功能正常

接下來可以執行完整的雷達通知流程。"""

    return send_text_notification(test_message)

if __name__ == "__main__":
    print("📱 氣象雷達 LINE 通知")
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # 測試模式
        success = test_notification()
        if success:
            print("✅ 測試完成")
        else:
            print("❌ 測試失敗")
            sys.exit(1)
    else:
        # 正常通知模式
        animation_info = load_animation_info()
        
        gif_path = None
        if animation_info:
            gif_path = animation_info.get('gif_path')
            print(f"📁 動畫檔案: {gif_path}")
        
        success = send_radar_animation(gif_path)
        
        if success:
            print("✅ 雷達通知發送完成")
            
            # 記錄發送歷史
            notification_log = {
                'timestamp': str(datetime.now()),
                'gif_path': gif_path,
                'success': True
            }
            
            with open('notification_log.json', 'w', encoding='utf-8') as f:
                json.dump(notification_log, f, ensure_ascii=False, indent=2)
                
        else:
            print("❌ 通知發送失敗")
            sys.exit(1)