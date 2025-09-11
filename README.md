# 台灣氣象雷達 LINE Bot

自動監控台灣氣象雷達資料，生成動畫並透過 LINE Bot 發送通知。

## 功能特色

- 📡 自動取得 NCDR 氣象雷達資料
- 🎬 生成雷達回波動畫 GIF
- 📱 透過 LINE Bot 推播通知
- ⏰ GitHub Actions 自動執行（每日 08:00 和 13:00）
- ☁️ 雲端圖片托管

## 安裝與設定

### 1. 複製專案

```bash
git clone https://github.com/your-username/weather-radar-line-bot.git
cd weather-radar-line-bot
```

### 2. 安裝依賴

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 環境變數設定

建立 `.env` 檔案：

```env
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token
LINE_CHANNEL_SECRET=your_channel_secret
LINE_USER_ID=your_user_id
```

### 4. LINE Bot 設定

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 建立新的 Provider 和 Messaging API Channel
3. 取得 Channel Access Token 和 Channel Secret
4. 取得你的 User ID

## 本地測試

```bash
python main.py
```

## GitHub Actions 自動化

1. 在 GitHub 專案設定中新增 Secrets：
   - `LINE_CHANNEL_ACCESS_TOKEN`
   - `LINE_CHANNEL_SECRET`
   - `LINE_USER_ID`

2. GitHub Actions 會自動在每日 08:00 和 13:00（台北時間）執行

## 專案結構

```
weather-radar-line-bot/
├── main.py                 # 主程式
├── src/
│   └── image_processor.py  # 圖片處理模組
├── config/
├── images/                 # 輸出圖片目錄
├── .github/
│   └── workflows/
│       └── weather-radar-notification.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 使用的 API

- **NCDR 氣象雷達**: https://watch.ncdr.nat.gov.tw/wh/cv_ncdrnowcast_info
- **LINE Messaging API**: 推播通知
- **catbox.moe**: 圖片託管服務

## 技術架構

1. **資料取得**: 從 NCDR API 取得雷達資料清單
2. **圖片下載**: 下載雷達圖片到本地
3. **動畫生成**: 使用 PIL 製作 GIF 動畫
4. **雲端上傳**: 上傳到 catbox.moe 取得公開網址
5. **LINE 通知**: 透過 LINE Bot 發送圖片訊息

## 注意事項

- 圖片會在本地暫存，定期自動清理
- GIF 動畫在 LINE 聊天室內可能顯示為靜態圖片，但分享後會正常播放
- 建議圖片大小控制在 600x480 以內，確保載入速度

## 授權

MIT License