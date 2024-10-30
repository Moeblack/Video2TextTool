import PyInstaller.__main__
import os
import sys
import shutil

# 获取 ffmpeg.exe 路径
ffmpeg_path = shutil.which('ffmpeg')
if not ffmpeg_path:
    print("错误: 未找到 ffmpeg，请先安装 ffmpeg 并确保其在系统 PATH 中")
    sys.exit(1)

PyInstaller.__main__.run([
    'gui.py',  # 主程序文件
    '--name=语音转文字工具',  # 生成的 exe 名称
    '--onefile',  # 打包成单个文件
    '--noconsole',  # 不显示控制台窗口
    '--add-binary=%s;.' % ffmpeg_path,  # 添加 ffmpeg
    # '--icon=icon.ico',  # 如果你有图标的话
    '--clean',  # 清理临时文件
    '--add-data=README.md;.',  # 添加说明文档
    '--hidden-import=PyQt5',
    '--hidden-import=PyQt5.QtCore',
    '--hidden-import=PyQt5.QtGui',
    '--hidden-import=PyQt5.QtWidgets',
    '--hidden-import=qfluentwidgets'
])