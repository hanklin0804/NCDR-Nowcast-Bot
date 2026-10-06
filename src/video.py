"""雷達圖合成：MP4 影片與預覽圖"""

import subprocess

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def make_video(frame_pattern, output_path, seconds_per_frame=0.6, width=1280):
    """將 frame_pattern 的連號圖片合成 LINE 可播放的 MP4（H.264 / yuv420p）"""
    subprocess.run([
        FFMPEG, "-y", "-loglevel", "error",
        "-framerate", f"1000/{int(seconds_per_frame * 1000)}",
        "-i", frame_pattern,
        "-vf", f"scale={width}:-2,setsar=1,format=yuv420p",
        "-r", "30",
        "-c:v", "libx264",
        "-movflags", "+faststart",
        output_path,
    ], check=True)


def make_preview(image_path, output_path, width=1280):
    """產生 LINE 預覽用的 JPEG（上限 1MB）"""
    subprocess.run([
        FFMPEG, "-y", "-loglevel", "error",
        "-i", image_path,
        "-vf", f"scale={width}:-2,setsar=1",
        "-q:v", "4",
        output_path,
    ], check=True)
