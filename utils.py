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
            '-ab', '192k',  # 音频比特率
            audio_path
        ]
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"FFmpeg 转换错误：{e}")
