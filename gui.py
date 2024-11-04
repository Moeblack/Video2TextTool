# gui.py

import sys
import os
import subprocess
import threading
from qfluentwidgets import FluentIcon as FIF
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QMessageBox, QSizePolicy
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QComboBox, QListWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QMimeData, QSize, QObject, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QDrag, QScreen
from qfluentwidgets import (FluentWindow, PushButton, ComboBox, ListWidget, StrongBodyLabel, 
                          SplitFluentWindow, SubtitleLabel, setTheme, Theme)

from bk_asr import BcutASR, JianYingASR, KuaiShouASR
from utils import convert_video_to_audio
from math import ceil
from datetime import timedelta

class SignalHandler(QObject):
    status_update = pyqtSignal(str)
    show_warning = pyqtSignal(str, str)
    show_critical = pyqtSignal(str, str)
    show_info = pyqtSignal(str, str)

class MainWindow(SplitFluentWindow):
    def __init__(self):
        super().__init__()
        
        # 设置主题
        setTheme(Theme.AUTO)
        
        # 获取屏幕DPI缩放比例
        screen = QApplication.primaryScreen()
        self.dpi_scale = screen.logicalDotsPerInch() / 96.0

        # 根据DPI缩放设置初始窗口大小
        self.resize(int(960 * self.dpi_scale), int(600 * self.dpi_scale))
        self.input_files = []
        # 设置侧边栏样式
        self.navigationInterface.setExpandWidth(int(280 * self.dpi_scale))
        self.navigationInterface.setMinimumWidth(int(60 * self.dpi_scale))
        # 修改导航栏样式，调整字体大小和按钮大小
        self.navigationInterface.setStyleSheet(f"""
            NavigationInterface {{
                background-color: rgb(243, 243, 243);
                padding: {int(6 * self.dpi_scale)}px;
            }}
            NavigationInterface QLabel {{
                font-size: {int(16 * self.dpi_scale)}px;
            }}
            NavigationInterface QPushButton {{
                padding: {int(12 * self.dpi_scale)}px;
                font-size: {int(16 * self.dpi_scale)}px;
                qproperty-iconSize: {int(28 * self.dpi_scale)}px {int(28 * self.dpi_scale)}px;
            }}
            NavigationInterface #backButton {{
                padding: {int(12 * self.dpi_scale)}px;
                font-size: {int(16 * self.dpi_scale)}px;
                qproperty-iconSize: {int(28 * self.dpi_scale)}px {int(28 * self.dpi_scale)}px;
            }}
            NavigationInterface #backButton:hover {{
                background-color: rgba(0, 0, 0, 0.1);
            }}
            NavigationInterface #menuItem {{
                font-size: {int(16 * self.dpi_scale)}px;
                font-weight: bold;
            }}
            NavigationInterface #menuItemLabel {{
                font-size: {int(16 * self.dpi_scale)}px;
                font-weight: bold;
            }}
        """)
        # 创建主窗口部件
        self.main_widget = QWidget()
        self.main_widget.setObjectName("mainInterface")
        self.addSubInterface(self.main_widget, 'main', '主页')
        
        # 添加信号处理器
        self.signal_handler = SignalHandler()
        self.signal_handler.status_update.connect(self.update_status)
        self.signal_handler.show_warning.connect(self.show_warning_dialog)
        self.signal_handler.show_critical.connect(self.show_critical_dialog)
        self.signal_handler.show_info.connect(self.show_info_dialog)
        
        self.init_ui()

    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(int(20 * self.dpi_scale), int(20 * self.dpi_scale), 
                                    int(20 * self.dpi_scale), int(20 * self.dpi_scale))
        main_layout.setSpacing(int(20 * self.dpi_scale))

        # 标题
        title = SubtitleLabel("字幕提取及文字稿生成", self)
        title.setFont(QFont("Segoe UI", int(24 * self.dpi_scale), QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # ASR引擎选择区域
        engine_layout = QHBoxLayout()
        engine_layout.setSpacing(int(10 * self.dpi_scale))
        
        self.engine_label = StrongBodyLabel("ASR 引擎：")
        self.engine_label.setFont(QFont("Microsoft YaHei", int(12 * self.dpi_scale)))
        engine_layout.addWidget(self.engine_label)
        
        self.engine_combo = ComboBox()
        self.engine_combo.addItems(["Bcut", "JianYing", "KuaiShou"])
        self.engine_combo.setMinimumWidth(int(200 * self.dpi_scale))
        self.engine_combo.setMinimumHeight(int(32 * self.dpi_scale))
        engine_layout.addWidget(self.engine_combo)
        engine_layout.addStretch()
        main_layout.addLayout(engine_layout)

        # 文件列表
        self.file_list = ListWidget()
        self.file_list.setAcceptDrops(True)
        self.file_list.dragEnterEvent = self.dragEnterEvent
        self.file_list.dropEvent = self.dropEvent
        self.file_list.setMinimumHeight(int(300 * self.dpi_scale))
        self.file_list.setStyleSheet(f"""
            ListWidget {{
                border: {int(1 * self.dpi_scale)}px solid #cccccc;
                border-radius: {int(4 * self.dpi_scale)}px;
                padding: {int(5 * self.dpi_scale)}px;
                font-size: {int(12 * self.dpi_scale)}px;
            }}
        """)
        main_layout.addWidget(self.file_list)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(int(10 * self.dpi_scale))

        # 左侧按钮组
        left_buttons = QHBoxLayout()
        self.add_file_btn = PushButton("添加文件", self)
        self.add_file_btn.setIcon(FIF.ADD)
        self.add_file_btn.clicked.connect(self.add_files)
        left_buttons.addWidget(self.add_file_btn)

        self.remove_file_btn = PushButton("删除文件", self)
        self.remove_file_btn.setIcon(FIF.DELETE)
        self.remove_file_btn.clicked.connect(self.remove_files)
        left_buttons.addWidget(self.remove_file_btn)
        
        button_layout.addLayout(left_buttons)
        button_layout.addStretch()

        # 右侧按钮组
        right_buttons = QHBoxLayout()
        self.output_combo = ComboBox()
        self.output_combo.addItems(["纯文本", "SRT字幕"])
        self.output_combo.setMinimumWidth(int(120 * self.dpi_scale))
        right_buttons.addWidget(self.output_combo)

        self.start_btn = PushButton("开始处理", self)
        self.start_btn.setIcon(FIF.PLAY)
        self.start_btn.clicked.connect(self.start_processing)
        right_buttons.addWidget(self.start_btn)
        
        button_layout.addLayout(right_buttons)
        main_layout.addLayout(button_layout)

        # 状态显示区域
        self.status_label = SubtitleLabel("")
        self.status_label.setObjectName("statusLabel")
        main_layout.addWidget(self.status_label)

        # 统一按钮样式
        for btn in [self.add_file_btn, self.remove_file_btn, self.start_btn]:
            btn.setMinimumHeight(int(32 * self.dpi_scale))
            btn.setMinimumWidth(int(120 * self.dpi_scale))
            btn.setIconSize(QSize(int(16 * self.dpi_scale), int(16 * self.dpi_scale)))

        

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 窗口大小变化时重新计算DPI缩放
        screen = QApplication.primaryScreen()
        self.dpi_scale = screen.logicalDotsPerInch() / 96.0
        # 更新UI元素大小
        self.update_ui_sizes()
    
    def update_ui_sizes(self):
        # 更新各个UI元素的大小
        self.engine_label.setFixedWidth(int(100 * self.dpi_scale))
        self.engine_combo.setMinimumWidth(int(200 * self.dpi_scale))
        self.file_list.setMinimumHeight(int(300 * self.dpi_scale))
        self.add_file_btn.setFixedWidth(int(120 * self.dpi_scale))
        self.remove_file_btn.setFixedWidth(int(120 * self.dpi_scale))
        self.start_btn.setFixedWidth(int(120 * self.dpi_scale))
        
        # 更新样式表
        self.setStyleSheet(f"""
            QWidget {{
                font-family: Microsoft YaHei;
            }}
            #titleLabel {{
                font-size: {int(24 * self.dpi_scale)}px;
                padding: {int(10 * self.dpi_scale)}px 0;
            }}
            #statusLabel {{
                font-size: {int(14 * self.dpi_scale)}px;
                color: #666666;
            }}
            ListWidget {{
                border: {int(1 * self.dpi_scale)}px solid #cccccc;
                border-radius: {int(5 * self.dpi_scale)}px;
            }}
            QPushButton {{
                min-height: {int(32 * self.dpi_scale)}px;
                font-size: {int(14 * self.dpi_scale)}px;
            }}
            QComboBox {{
                min-height: {int(32 * self.dpi_scale)}px;
                font-size: {int(14 * self.dpi_scale)}px;
            }}
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path and file_path not in self.input_files:
                self.input_files.append(file_path)
                self.file_list.addItem(file_path)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", "音频/视频文件 (*.mp4 *.avi *.mov *.mp3 *.wav *.m4a *.m4v)")
        if files:
            for file in files:
                if file not in self.input_files:
                    self.input_files.append(file)
                    self.file_list.addItem(file)

    def remove_files(self):
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            self.input_files.remove(item.text())
            self.file_list.takeItem(self.file_list.row(item))

    def start_processing(self):
        if not self.input_files:
            QMessageBox.warning(self, "提示", "请先添加需要处理的文件。")
            return

        engine_name = self.engine_combo.currentText()
        api_key = ''  # 如果需要 API Key，可以在这里添加输入框获取

        self.asr_engine = self.initialize_asr_engine(engine_name, api_key)

        # 使用线程避免界面卡顿
        threading.Thread(target=self.process_files, daemon=True).start()

    def initialize_asr_engine(self, engine_name, api_key=None):
        if engine_name == "Bcut":
            return BcutASR
        elif engine_name == "JianYing":
            return JianYingASR
        elif engine_name == "KuaiShou":
            return KuaiShouASR
        else:
            raise ValueError("不支持的 ASR 引擎")

    def process_files(self):
        output_type = self.output_combo.currentText()
        has_error = False
        
        try:
            for file_path in self.input_files:
                try:
                    file_name = os.path.splitext(os.path.basename(file_path))[0]
                    temp_audio = os.path.join(os.path.dirname(file_path), f"{file_name}_temp_audio.mp3")
                    
                    # 转换视频为音频
                    if os.path.splitext(file_path)[1].lower() in ['.mp4', '.avi', '.mov', '.m4v', '.flv', '.mkv']:
                        try:
                            self.signal_handler.status_update.emit(f"正在将视频转换为音频：{file_path}")
                            convert_video_to_audio(file_path, temp_audio)
                        except Exception as e:
                            raise Exception(f"视频转换失败: {str(e)}")
                    else:
                        temp_audio = file_path

                    # 分析音频时长
                    try:
                        self.signal_handler.status_update.emit("正在分析音频时长...")
                        import ffmpeg
                        probe = ffmpeg.probe(temp_audio)
                        duration = float(probe['format']['duration'])
                        chunk_duration = 45 * 60  # 45分钟
                        num_chunks = ceil(duration / chunk_duration)
                    except Exception as e:
                        raise Exception(f"分析音频时长失败: {str(e)}")

                    # 逐段处理
                    all_results = []
                    base_name = os.path.splitext(temp_audio)[0]
                    
                    for i in range(num_chunks):
                        try:
                            start_time = i * chunk_duration
                            chunk_file = f"{base_name}_part_{i+1}.mp3"
                            
                            # 分割当前段
                            self.signal_handler.status_update.emit(f"正在分割第 {i+1}/{num_chunks} 段音频...")
                            stream = ffmpeg.input(temp_audio, ss=start_time, t=chunk_duration)
                            stream = ffmpeg.output(stream, chunk_file)
                            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
                            
                            # 立即处理当前段
                            self.signal_handler.status_update.emit(f"正在识别第 {i+1}/{num_chunks} 段音频...")
                            asr_instance = self.asr_engine(chunk_file)
                            result = asr_instance.run()
                            
                            if result and result.has_data():
                                all_results.append(result)
                            else:
                                raise Exception(f"第 {i+1} 段ASR处理返回空结果")
                            
                        except Exception as e:
                            raise Exception(f"处理第 {i+1} 段时出错: {str(e)}")
                        finally:
                            if os.path.exists(chunk_file):
                                try:
                                    os.remove(chunk_file)
                                except:
                                    pass

                    # 验证是否有有效结果
                    if not all_results:
                        raise Exception("没有获取到有效的识别结果")
                    
                    # 合并结果并保存
                    try:
                        if output_type == "纯文本":
                            output_file = os.path.join(os.path.dirname(file_path), f"{file_name}.txt")
                            with open(output_file, 'w', encoding='utf-8') as f:
                                for result in all_results:
                                    text = result.to_txt()
                                    if text:
                                        f.write(text + "\n")
                        else:  # SRT字幕
                            output_file = os.path.join(os.path.dirname(file_path), f"{file_name}.srt")
                            with open(output_file, 'w', encoding='utf-8') as f:
                                offset = 0
                                for i, result in enumerate(all_results):
                                    if i > 0:
                                        offset += 45 * 60 * 1000
                                    adjusted_segments = []
                                    for seg in result.segments:
                                        seg.start_time += offset
                                        seg.end_time += offset
                                        adjusted_segments.append(seg)
                                    result.segments = adjusted_segments
                                    srt = result.to_srt()
                                    if srt:
                                        f.write(srt + "\n")
                                    
                            self.signal_handler.status_update.emit(f"处理完成，结果已保存为：{output_file}")
                    except Exception as e:
                        raise Exception(f"保存结果失败: {str(e)}")
                    
                except Exception as e:
                    has_error = True
                    error_msg = f"处理文件 {file_path} 时出错: {str(e)}"
                    self.signal_handler.status_update.emit(error_msg)
                    self.signal_handler.show_warning.emit("错误", error_msg)
                    continue
                finally:
                    if os.path.exists(temp_audio) and temp_audio != file_path:
                        try:
                            os.remove(temp_audio)
                        except:
                            pass
            
            final_message = "全部文件处理完成！" if not has_error else "处理完成，但有部分文件出现错误，请查看详细信息。"
            self.signal_handler.status_update.emit(final_message)
            if not has_error:
                self.signal_handler.show_info.emit("完成", final_message)
            
        except Exception as e:
            error_msg = f"发生严重错误: {str(e)}"
            self.signal_handler.status_update.emit(error_msg)
            self.signal_handler.show_critical.emit("错误", error_msg)

    def update_status(self, message):
        self.status_label.setText(message)
        print(message)

    def show_warning_dialog(self, title, message):
        QMessageBox.warning(self, title, message)
        
    def show_critical_dialog(self, title, message):
        QMessageBox.critical(self, title, message)
        
    def show_info_dialog(self, title, message):
        QMessageBox.information(self, title, message)

if __name__ == "__main__":
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
