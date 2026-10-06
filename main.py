#!/usr/bin/env python3
"""雷達回波動畫 LINE 推播

  python main.py build                    產出 site/<name>.mp4 與 site/<name>.jpg
  python main.py push <base_url> <name>   推播文字＋影片
  python main.py notify-failure           推播失敗通知
"""

import os
import sys
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from src.line_push import push_messages
from src.ncdr import download_frames, fetch_frame_paths, latest_observation
from src.video import make_preview, make_video

SITE_DIR = "site"
TAIPEI = ZoneInfo("Asia/Taipei")


def build():
    paths = fetch_frame_paths()
    preview_index, stamp = latest_observation(paths)
    name = f"radar_{stamp}"
    os.makedirs(SITE_DIR, exist_ok=True)

    with tempfile.TemporaryDirectory() as frame_dir:
        frame_pattern = os.path.join(frame_dir, "frame_%02d.png")
        frames = download_frames(paths, frame_pattern)
        make_video(frame_pattern, f"{SITE_DIR}/{name}.mp4")
        make_preview(frames[preview_index], f"{SITE_DIR}/{name}.jpg")

    print(f"✅ 已產出 {SITE_DIR}/{name}.mp4、{SITE_DIR}/{name}.jpg")
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"name={name}\n")


def push(base_url, name):
    base_url = base_url.rstrip("/")
    timestamp = datetime.now(TAIPEI).strftime("%Y/%m/%d %H:%M")
    push_messages(os.environ["LINE_CHANNEL_ACCESS_TOKEN"], os.environ["LINE_USER_ID"], [
        {"type": "text", "text": f"🌧️ 雷達回波動畫 ({timestamp})"},
        {
            "type": "video",
            "originalContentUrl": f"{base_url}/{name}.mp4",
            "previewImageUrl": f"{base_url}/{name}.jpg",
        },
    ])
    print("✅ LINE 推播完成")


def notify_failure():
    text = "❌ 雷達推播失敗"
    run_url = os.getenv("RUN_URL")
    if run_url:
        text += f"\n{run_url}"
    push_messages(os.environ["LINE_CHANNEL_ACCESS_TOKEN"], os.environ["LINE_USER_ID"], [
        {"type": "text", "text": text},
    ])


def main():
    load_dotenv()
    command, args = sys.argv[1] if len(sys.argv) > 1 else None, sys.argv[2:]

    if command == "build" and not args:
        build()
    elif command == "push" and len(args) == 2:
        push(*args)
    elif command == "notify-failure" and not args:
        notify_failure()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
