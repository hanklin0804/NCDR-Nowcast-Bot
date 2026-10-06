"""NCDR 臨近預報雷達圖：取得清單與下載"""

import os
import re
from urllib.parse import urljoin

import requests

BASE_URL = "https://watch.ncdr.nat.gov.tw"
LIST_URL = f"{BASE_URL}/wh/cv_ncdrnowcast_info"
OBSERVATION_PATTERN = re.compile(r"oLI_s(\d{12})\.png$")


def fetch_frame_paths():
    """取得雷達圖路徑清單，照 NCDR 回傳順序（3 張觀測 + 13 張預報）"""
    response = requests.get(LIST_URL, timeout=10)
    response.raise_for_status()

    lines = response.text.strip().splitlines()[1:]  # 第一行是表頭
    paths = [line.split(",")[2].strip() for line in lines if line.strip()]
    if not paths:
        raise RuntimeError(f"NCDR 清單沒有資料: {response.text[:200]}")
    return paths


def latest_observation(paths):
    """回傳最新一張觀測圖的 (索引, NCDR 時間戳 yyyymmddHHMM)"""
    for index in range(len(paths) - 1, -1, -1):
        match = OBSERVATION_PATTERN.search(paths[index])
        if match:
            return index, match.group(1)
    raise RuntimeError("NCDR 清單裡沒有觀測圖")


def download_frames(paths, frame_pattern):
    """依序下載到 frame_pattern % 索引，回傳本機檔案路徑"""
    os.makedirs(os.path.dirname(frame_pattern), exist_ok=True)
    files = []
    for index, path in enumerate(paths):
        response = requests.get(urljoin(BASE_URL, path), timeout=30)
        response.raise_for_status()
        local_path = frame_pattern % index
        with open(local_path, "wb") as f:
            f.write(response.content)
        files.append(local_path)
        print(f"[{index + 1}/{len(paths)}] {os.path.basename(path)} ({len(response.content):,} bytes)")
    return files
