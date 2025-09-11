#!/usr/bin/env python3
"""取得氣象雷達資料"""

import json
import sys
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("❌ 缺少 requests 套件: pip install requests")
    sys.exit(1)

def get_radar_data():
    """取得最新氣象雷達資料列表"""
    
    # 基於你提供的資料格式，先使用模擬資料
    # 實際使用時需要找到真正的 API endpoint
    
    now = datetime.now()
    base_time = now.replace(minute=(now.minute // 10) * 10, second=0, microsecond=0)
    
    radar_data = []
    
    # 觀測圖片 (過去 30 分鐘, 每 10 分鐘一張)
    for i in range(-3, 0):
        time_point = base_time + timedelta(minutes=i*10)
        timestamp = time_point.strftime("%Y-%m-%d %H:%M")
        filename = f"oLI_s{time_point.strftime('%Y%m%d%H%M')}.png"
        file_path = f"/00_Wxmap/7F13_NOWCAST/OBS/{time_point.strftime('%Y%m')}/{time_point.strftime('%Y%m%d')}/{filename}"
        
        radar_data.append({
            "id": i,
            "timestamp": timestamp,
            "file": file_path,
            "size": 1,
            "file_size": 0
        })
    
    # 預測圖片 (未來 2 小時, 每 10 分鐘一張)
    for i in range(0, 13):
        time_point = base_time + timedelta(minutes=i*10)
        timestamp = time_point.strftime("%Y-%m-%d %H:%M")
        time_dir = time_point.strftime('%Y%m%d%H%M')
        filename = f"nowcast_{time_dir}_s{i:02d}.png"
        file_path = f"/00_Wxmap/7F13_NOWCAST/{time_point.strftime('%Y%m')}/{time_point.strftime('%Y%m%d')}/{time_dir}/{filename}"
        
        # 模擬檔案大小 (KB)
        file_size = 270000 - (i * 1000)
        
        radar_data.append({
            "id": i,
            "timestamp": timestamp,
            "file": file_path,
            "size": 1,
            "file_size": file_size
        })
    
    return radar_data

def fetch_radar_data_from_api():
    """從 NCDR 實際 API 取得資料"""
    
    api_url = "https://watch.ncdr.nat.gov.tw/wh/cv_ncdrnowcast_info"
    
    try:
        print(f"🔍 嘗試 NCDR API: {api_url}")
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        # 解析 CSV 格式資料
        lines = response.text.strip().split('\n')
        radar_data = []
        
        for line in lines:
            if line.strip():
                # 解析 CSV 格式: id,timestamp,file,size,file_size
                parts = line.split(',')
                if len(parts) >= 4:
                    try:
                        item = {
                            'id': int(parts[0]),
                            'timestamp': parts[1].strip(),
                            'file': parts[2].strip(),
                            'size': int(parts[3]) if parts[3].isdigit() else 1,
                            'file_size': int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
                        }
                        radar_data.append(item)
                    except (ValueError, IndexError) as e:
                        print(f"⚠️ 跳過無效資料行: {line} ({e})")
                        continue
        
        if radar_data:
            print(f"✅ API 成功取得 {len(radar_data)} 筆資料")
            return radar_data
        else:
            print("⚠️ API 回應無有效資料")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API 連線失敗: {e}")
        return None
    except Exception as e:
        print(f"❌ 資料解析錯誤: {e}")
        return None

def save_radar_data(data, filename="radar_data.json"):
    """儲存雷達資料到檔案"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 資料已儲存到: {filename}")

if __name__ == "__main__":
    print("📡 取得氣象雷達資料...")
    
    # 先嘗試真實 API
    api_data = fetch_radar_data_from_api()
    
    if api_data:
        print("✅ 使用 API 資料")
        data = api_data
    else:
        print("🔄 使用模擬資料")
        data = get_radar_data()
    
    # 顯示資料摘要
    print(f"\n📊 資料摘要:")
    print(f"   總圖片數: {len(data)}")
    
    if isinstance(data, list) and len(data) > 0:
        obs_count = len([item for item in data if item.get('id', 0) < 0])
        pred_count = len([item for item in data if item.get('id', 0) >= 0])
        print(f"   觀測圖片: {obs_count}")
        print(f"   預測圖片: {pred_count}")
    
    # 儲存資料
    save_radar_data(data)
    
    # 顯示前幾筆資料
    print(f"\n📋 範例資料:")
    if isinstance(data, list) and len(data) > 0:
        for i, item in enumerate(data[:3]):
            print(f"   {i+1}. ID:{item.get('id', 'N/A')} - {item.get('timestamp', 'N/A')}")
            print(f"      檔案: {item.get('file', 'N/A')}")
    
    print("\n✅ 雷達資料處理完成")