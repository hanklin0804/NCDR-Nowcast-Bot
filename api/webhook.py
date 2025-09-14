from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import hashlib
import hmac
import base64
from datetime import datetime

# 引用現有模組
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.image_processor import process_radar_images

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 讀取請求
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)

            # 驗證 LINE 簽章
            signature = self.headers.get('X-Line-Signature', '')
            if not self._verify_signature(body, signature):
                self.send_response(403)
                self.end_headers()
                return

            # 解析事件
            data = json.loads(body.decode('utf-8'))
            for event in data.get('events', []):
                if event.get('type') == 'message' and event.get('message', {}).get('type') == 'text':
                    self._handle_message(event['replyToken'])

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')

        except Exception as e:
            print(f"Error: {e}")
            self.send_response(500)
            self.end_headers()

    def _verify_signature(self, body, signature):
        """驗證 LINE Webhook 簽章"""
        secret = os.getenv('LINE_CHANNEL_SECRET')
        if not secret:
            return False

        hash_digest = hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).digest()
        expected = base64.b64encode(hash_digest).decode('utf-8')

        return signature == expected

    def _handle_message(self, reply_token):
        """處理訊息：生成雷達圖並回應"""
        try:
            print("Starting radar processing...")

            # 直接在這裡實作雷達資料取得，避免導入問題
            radar_data = self._fetch_radar_data()
            print(f"Radar data count: {len(radar_data) if radar_data else 0}")

            if not radar_data:
                print("No radar data found")
                self._send_error(reply_token, "❌ 無法取得雷達資料")
                return

            # 處理圖片 - 使用 /tmp 目錄
            import tempfile
            import os

            # 設定暫存目錄為 /tmp（Vercel Serverless 可寫入）
            original_output_dir = "images"
            temp_output_dir = "/tmp/images"
            os.makedirs(temp_output_dir, exist_ok=True)

            # 調用處理函數，但指定使用 /tmp 目錄
            result = self._process_radar_images_serverless(radar_data[-8:])
            print(f"Process result: {result}")

            if not result or not result.get('image_url'):
                print("Image processing failed")
                self._send_error(reply_token, "❌ 雷達圖處理失敗，請稍後再試")
                return

            print(f"Image URL: {result['image_url']}")
            # 發送雷達圖
            self._send_radar_image(reply_token, result['image_url'])

        except Exception as e:
            print(f"Handle message error: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            self._send_error(reply_token, "❌ 系統暫時無法處理，請稍後再試")

    def _fetch_radar_data(self):
        """取得雷達資料"""
        try:
            import requests
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

            return radar_data

        except Exception as e:
            print(f"Error fetching radar data: {e}")
            return []

    def _process_radar_images_serverless(self, radar_data):
        """Serverless 版本的雷達圖片處理"""
        import requests
        import tempfile
        from PIL import Image
        from urllib.parse import urljoin

        if not radar_data:
            return None

        base_url = "https://watch.ncdr.nat.gov.tw"
        images = []

        print(f"Processing {len(radar_data)} radar images...")

        # 下載並處理圖片（直接在記憶體中）
        for i, item in enumerate(radar_data, 1):
            try:
                file_path = item.get('file', '')
                if not file_path:
                    continue

                image_url = urljoin(base_url, file_path)
                print(f"[{i}/{len(radar_data)}] Downloading: {image_url}")

                response = requests.get(image_url, timeout=30)
                response.raise_for_status()

                # 直接從記憶體處理圖片
                from io import BytesIO
                img = Image.open(BytesIO(response.content))
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # 調整大小
                img.thumbnail((600, 480), Image.Resampling.LANCZOS)
                images.append(img)
                print(f"[{i}/{len(radar_data)}] Processed successfully")

            except Exception as e:
                print(f"Error processing image {i}: {e}")
                continue

        if not images:
            print("No images processed successfully")
            return None

        # 生成 GIF（使用 /tmp 暫存檔案）
        try:
            with tempfile.NamedTemporaryFile(suffix='.gif', delete=False, dir='/tmp') as tmp_file:
                gif_path = tmp_file.name

            print(f"Creating GIF with {len(images)} frames...")
            images[0].save(
                gif_path,
                save_all=True,
                append_images=images[1:],
                duration=600,
                loop=0,
                optimize=True
            )

            # 上傳到 catbox.moe
            image_url = self._upload_to_catbox(gif_path)

            # 清理暫存檔
            import os
            try:
                os.unlink(gif_path)
            except:
                pass

            return {
                'gif_path': gif_path,
                'image_url': image_url,
                'downloaded_count': len(images)
            }

        except Exception as e:
            print(f"Error creating GIF: {e}")
            return None

    def _upload_to_catbox(self, file_path):
        """上傳檔案到 catbox.moe"""
        try:
            import requests
            print(f"Uploading to catbox.moe...")

            with open(file_path, 'rb') as f:
                files = {'fileToUpload': f}
                data = {'reqtype': 'fileupload'}
                response = requests.post(
                    'https://catbox.moe/user/api.php',
                    files=files,
                    data=data,
                    timeout=30
                )

            if response.status_code == 200 and response.text.startswith('https://'):
                url = response.text.strip()
                print(f"Upload successful: {url}")
                return url
            else:
                print(f"Upload failed: {response.status_code}, {response.text}")

        except Exception as e:
            print(f"Error uploading to catbox: {e}")

        return None

    def _send_radar_image(self, reply_token, image_url):
        """發送雷達圖片"""
        import requests

        timestamp = datetime.now().strftime("%Y/%m/%d %H:%M")

        payload = {
            'replyToken': reply_token,
            'messages': [
                {
                    'type': 'text',
                    'text': f'🌧️ 最新雷達回波動畫 ({timestamp})'
                },
                {
                    'type': 'image',
                    'originalContentUrl': image_url,
                    'previewImageUrl': image_url
                }
            ]
        }

        headers = {
            'Authorization': f'Bearer {os.getenv("LINE_CHANNEL_ACCESS_TOKEN")}',
            'Content-Type': 'application/json'
        }

        response = requests.post(
            'https://api.line.me/v2/bot/message/reply',
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        response.raise_for_status()

    def _send_error(self, reply_token, text):
        """發送錯誤訊息"""
        import requests

        payload = {
            'replyToken': reply_token,
            'messages': [{'type': 'text', 'text': text}]
        }

        headers = {
            'Authorization': f'Bearer {os.getenv("LINE_CHANNEL_ACCESS_TOKEN")}',
            'Content-Type': 'application/json'
        }

        requests.post(
            'https://api.line.me/v2/bot/message/reply',
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )