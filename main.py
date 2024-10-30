# main.py

import os
import sys
import subprocess
from bk_asr import BcutASR, JianYingASR, KuaiShouASR
from utils import convert_video_to_audio

def main():
    # 用户配置部分
    input_files = [
        # 在这里添加您要处理的文件路径，支持视频和音频文件
        'path/to/your/video_or_audio_file1',
        'path/to/your/video_or_audio_file2',
    ]
    output_format = 'txt'  # 输出文字稿格式，可选 'txt' 或 'srt'
    asr_engine_name = 'Bcut'  # 选择 ASR 引擎，可选 'Bcut', 'JianYing', 'KuaiShou'
    api_key = ''  # 如果需要 ASR 引擎的 API Key，可以在这里设置

    # 检查输入文件列表是否为空
    if not input_files:
        print("请在配置中指定需要处理的文件列表（input_files）。")
        sys.exit(1)

    # 初始化 ASR 引擎
    def initialize_asr_engine(engine_name, api_key=None):
        if engine_name == "Bcut":
            return BcutASR(api_key=api_key)
        elif engine_name == "JianYing":
            return JianYingASR(api_key=api_key)
        elif engine_name == "KuaiShou":
            return KuaiShouASR(api_key=api_key)
        else:
            raise ValueError("不支持的 ASR 引擎")

    asr_engine = initialize_asr_engine(asr_engine_name, api_key)

    for file_path in input_files:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            continue

        file_name, file_ext = os.path.splitext(os.path.basename(file_path))
        # 如果是视频文件，先转换为音频
        if file_ext.lower() in ['.mp4', '.avi', '.mov', '.m4v', '.flv', '.mkv']:
            audio_file = f"{file_name}.mp3"
            try:
                print(f"正在将视频文件转换为音频：{file_path}")
                convert_video_to_audio(file_path, audio_file)
            except subprocess.CalledProcessError:
                print(f"转换失败：{file_path}")
                continue
        else:
            audio_file = file_path  # 如果是音频文件，直接使用

        # 使用 ASR 引擎进行语音识别
        try:
            print(f"正在处理文件：{audio_file}")
            asr_engine.audio_file = audio_file
            result = asr_engine.run()
            # 将结果保存为文本文件
            if output_format == 'txt':
                output_file = f"{file_name}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.to_txt())
            elif output_format == 'srt':
                output_file = f"{file_name}.srt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.to_srt())
            print(f"处理完成，结果已保存为：{output_file}")
        except Exception as e:
            print(f"处理文件时出错：{audio_file}")
            print(f"错误信息：{e}")
            continue

if __name__ == "__main__":
    main()
