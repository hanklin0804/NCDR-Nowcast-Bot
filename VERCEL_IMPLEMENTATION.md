# LINE Bot 雷達圖 Vercel Serverless 實作指南

## 🎯 目標
在現有定時推播功能基礎上，新增即時回應功能：用戶對 LINE Bot 發送任何訊息，立即收到最新雷達動畫。

## 📋 功能設計
- ✅ **保留原有**: GitHub Actions 定時推播（08:00、11:30、14:00）
- ✅ **新增即時**: 用戶發訊息 → 即時回應雷達圖
- ✅ **零影響**: 不修改現有程式碼

## 🚀 實作步驟（5步完成）

### 步驟 1: 建立 Vercel 設定
建立 `vercel.json`：
```json
{
  "functions": {
    "api/webhook.py": {
      "runtime": "python3.9",
      "maxDuration": 30
    }
  }
}
```

### 步驟 2: 建立 Webhook API
建立 `api/webhook.py`：
```python
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
            # 取得雷達資料（重用現有函數）
            from main import fetch_radar_data
            radar_data = fetch_radar_data()

            if not radar_data:
                self._send_error(reply_token, "❌ 無法取得雷達資料")
                return

            # 處理圖片（重用現有函數）
            result = process_radar_images(radar_data[-8:])  # 取最新8張

            if not result or not result.get('image_url'):
                self._send_error(reply_token, "❌ 雷達圖處理失敗，請稍後再試")
                return

            # 發送雷達圖
            self._send_radar_image(reply_token, result['image_url'])

        except Exception as e:
            print(f"Handle message error: {e}")
            self._send_error(reply_token, "❌ 系統暫時無法處理，請稍後再試")

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
```

### 步驟 3: 部署到 Vercel
```bash
# 安裝 Vercel CLI
npm install -g vercel

# 部署
vercel --prod

# 在 Vercel Dashboard 設定環境變數：
# LINE_CHANNEL_ACCESS_TOKEN=你的token
# LINE_CHANNEL_SECRET=你的secret
```

### 步驟 4: 設定 LINE Webhook
1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 進入你的 Messaging API Channel
3. 設定 Webhook URL: `https://your-app.vercel.app/api/webhook`
4. 啟用 "Use webhook"
5. 停用 "Auto-reply messages"

### 步驟 5: 測試功能
- 對 LINE Bot 發送任何訊息
- 應該立即收到最新雷達動畫

## ⚠️ 重要提醒

### Vercel 限制
- 免費版：執行時間最長 10 秒
- Pro 版：執行時間最長 30 秒
- 圖片處理需要 15-25 秒，**建議使用 Pro 版**

### 成本估算
- **Vercel Pro**: $20/月（推薦，避免超時）
- **Vercel Hobby**: 免費（可能會超時失敗）

## 🔧 疑難排解

### 常見問題
1. **超時失敗**: 升級到 Vercel Pro 或減少處理圖片數量
2. **Webhook 驗證失敗**: 檢查 `LINE_CHANNEL_SECRET` 設定
3. **圖片無法顯示**: 檢查 catbox.moe 上傳是否成功

### 除錯方式
在 Vercel Dashboard → Functions → 查看執行記錄

## 🎉 完成！

現在你的 LINE Bot 具備：
- ⏰ **定時推播**：GitHub Actions 每日自動推播
- 💬 **即時回應**：用戶主動詢問立即回覆
- 🔄 **雙重保障**：兩套系統互為備援

**總開發時間**：約 2-3 小時
**檔案異動**：僅新增 2 個檔案，不影響現有功能