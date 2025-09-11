#!/usr/bin/env python3
"""圖片處理模組 - 整合圖片下載和動畫生成功能"""

import os
import sys
import json
import glob
from datetime import datetime
from urllib.parse import urljoin

try:
    import requests
    from PIL import Image
except ImportError as e:
    print(f"❌ 缺少必要套件: {e}")
    print("請安裝: pip install requests pillow")
    sys.exit(1)


def download_radar_images(image_list, base_url="https://watch.ncdr.nat.gov.tw", download_dir="temp"):
    """下載雷達圖片到本地"""
    
    if not image_list:
        print("❌ 沒有圖片清單")
        return []
    
    # 確保下載目錄存在
    os.makedirs(download_dir, exist_ok=True)
    
    downloaded_files = []
    failed_downloads = []
    
    print(f"⬇️ 開始下載 {len(image_list)} 個檔案...")
    
    for i, item in enumerate(image_list, 1):
        if not isinstance(item, dict):
            print(f"❌ 跳過無效項目: {item}")
            continue
            
        file_path = item.get('file', '')
        item_id = item.get('id', i)
        
        if not file_path:
            print(f"❌ 跳過空檔案路徑: {item}")
            continue
        
        # 建構完整 URL
        image_url = urljoin(base_url, file_path)
        
        # 建立本地檔名
        original_filename = os.path.basename(file_path)
        local_filename = f"{item_id:03d}_{original_filename}"
        local_path = os.path.join(download_dir, local_filename)
        
        try:
            print(f"[{i}/{len(image_list)}] 下載: {original_filename}")
            
            # 下載檔案
            response = requests.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # 儲存檔案
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(local_path)
            print(f"           ✅ 完成: {local_filename} ({file_size:,} bytes)")
            
            downloaded_files.append({
                'local_path': local_path,
                'original_url': image_url,
                'id': item_id,
                'size': file_size
            })
            
        except requests.exceptions.RequestException as e:
            error_msg = f"網路錯誤: {e}"
            print(f"           ❌ 失敗: {error_msg}")
            failed_downloads.append({
                'url': image_url,
                'error': error_msg,
                'id': item_id
            })
            
        except Exception as e:
            error_msg = f"檔案處理錯誤: {e}"
            print(f"           ❌ 失敗: {error_msg}")
            failed_downloads.append({
                'url': image_url,
                'error': error_msg,
                'id': item_id
            })
    
    # 摘要報告
    print(f"\n📊 下載摘要:")
    print(f"   成功: {len(downloaded_files)}")
    print(f"   失敗: {len(failed_downloads)}")
    
    return downloaded_files


def create_radar_gif(image_files, output_path="images/radar_animation.gif", duration=600, max_size=(600, 480)):
    """將雷達圖片合成為 GIF 動畫"""
    
    if not image_files:
        print("❌ 沒有圖片可以製作動畫")
        return None
    
    print(f"🎬 開始製作動畫，共 {len(image_files)} 張圖片...")
    
    # 按檔名排序（確保時間順序）
    image_files.sort()
    
    images = []
    total_frames = 0
    
    for i, file_path in enumerate(image_files, 1):
        try:
            print(f"[{i}/{len(image_files)}] 處理: {os.path.basename(file_path)}")
            
            # 開啟圖片
            img = Image.open(file_path)
            
            # 轉換為 RGB (GIF 需要)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 調整圖片大小（如果需要）
            if max_size and img.size != max_size:
                # 保持比例縮放
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                print(f"           調整大小: {img.size}")
            
            images.append(img)
            total_frames += 1
            
        except Exception as e:
            print(f"           ❌ 無法處理圖片 {file_path}: {e}")
            continue
    
    if not images:
        print("❌ 沒有有效的圖片可以製作動畫")
        return None
    
    try:
        # 確保輸出目錄存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        print(f"💾 儲存 GIF 動畫: {output_path}")
        print(f"   總幀數: {total_frames}")
        print(f"   每幀時長: {duration}ms")
        print(f"   總時長: {(total_frames * duration) / 1000:.1f}s")
        
        # 儲存為 GIF - 最簡單的設定
        images[0].save(
            output_path,
            save_all=True,
            append_images=images[1:],
            duration=duration,  # 每張圖片顯示時間 (毫秒)
            loop=0,  # 無限循環
            optimize=True  # 優化檔案大小
        )
        
        # 檢查檔案大小
        file_size = os.path.getsize(output_path)
        print(f"✅ GIF 動畫已建立: {output_path}")
        print(f"   檔案大小: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
        
        return output_path
        
    except Exception as e:
        print(f"❌ 儲存 GIF 失敗: {e}")
        return None


def upload_to_catbox(image_path):
    """上傳圖片到 catbox.moe"""
    try:
        print(f"📤 上傳到 catbox.moe: {os.path.basename(image_path)}")
        
        with open(image_path, 'rb') as f:
            files = {'fileToUpload': f}
            data = {'reqtype': 'fileupload'}
            response = requests.post('https://catbox.moe/user/api.php', 
                                   files=files, data=data, timeout=30)
        
        if response.status_code == 200 and response.text.startswith('https://'):
            url = response.text.strip()
            print(f"✅ 上傳成功: {url}")
            return url
                
    except Exception as e:
        print(f"❌ catbox.moe 上傳失敗: {e}")
    
    return None


def cleanup_temp_files(download_dir="temp", keep_recent=5):
    """清理舊的暫存檔案"""
    try:
        if not os.path.exists(download_dir):
            return
            
        files = []
        for filename in os.listdir(download_dir):
            file_path = os.path.join(download_dir, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files.append((file_path, stat.st_mtime))
        
        # 按修改時間排序，保留最新的檔案
        files.sort(key=lambda x: x[1], reverse=True)
        
        if len(files) > keep_recent:
            for file_path, _ in files[keep_recent:]:
                os.remove(file_path)
                print(f"🗑️ 清理舊檔案: {os.path.basename(file_path)}")
                
    except Exception as e:
        print(f"⚠️ 清理檔案時發生錯誤: {e}")


def process_radar_images(radar_data, output_dir="images"):
    """完整的雷達圖片處理流程"""
    
    print("🖼️ 開始雷達圖片處理流程...")
    
    # 1. 下載圖片
    downloaded_files = download_radar_images(radar_data)
    
    if not downloaded_files:
        print("❌ 沒有成功下載任何圖片")
        return None
    
    # 2. 生成動畫
    image_paths = [item['local_path'] for item in downloaded_files]
    gif_path = create_radar_gif(
        image_paths,
        output_path=f"{output_dir}/radar_latest.gif",
        duration=600,
        max_size=(600, 480)
    )
    
    if not gif_path:
        print("❌ 動畫生成失敗")
        return None
    
    # 3. 上傳到雲端
    image_url = upload_to_catbox(gif_path)
    
    # 4. 清理暫存檔案
    cleanup_temp_files()
    
    # 5. 儲存處理記錄
    processing_info = {
        'timestamp': datetime.now().isoformat(),
        'downloaded_files': len(downloaded_files),
        'gif_path': gif_path,
        'image_url': image_url,
        'file_size': os.path.getsize(gif_path) if os.path.exists(gif_path) else 0
    }
    
    with open(f"{output_dir}/processing_log.json", 'w', encoding='utf-8') as f:
        json.dump(processing_info, f, ensure_ascii=False, indent=2)
    
    print("✅ 雷達圖片處理完成")
    
    return {
        'gif_path': gif_path,
        'image_url': image_url,
        'downloaded_count': len(downloaded_files)
    }