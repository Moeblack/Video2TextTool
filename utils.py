# utils.py

import subprocess

def convert_video_to_audio(video_path, audio_path):
    """将视频文件转换为音频文件"""
    try:
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # 不处理视频
            '-acodec', 'libmp3lame',  # 使用 libmp3lame 编码器
            '-ab', '128k',  # 降低音频比特率到 128k
            '-ar', '44100',  # 设置采样率为 44.1kHz
            '-ac', '2',      # 设置为双声道
            '-q:a', '4',     # 设置音质等级 (0-9, 2-5较好)
            audio_path
        ]
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"FFmpeg 转换错误：{e}")
