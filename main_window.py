import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QApplication, QMessageBox
from PyQt5.QtCore import Qt
from todo_widget import TodoWidget
from english_widget import EnglishWidget

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(600, 800)  # 初始大小，后面根据功能动态调整
        self.move_to_top_right()

        # 加载配置
        self.config = self.load_config()

        # 布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(0)   # 无缝衔接

        # 存储子组件引用
        self.todo_widget = None
        self.english_widget = None

        # 右上角按钮（悬浮，不加入布局）
        self.setting_btn = QPushButton("⚙", self)
        self.setting_btn.setFixedSize(36, 36)
        self.setting_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,180);
                border: 1px solid rgba(200,200,200,150);
                border-radius: 18px;
                font-size: 16px;
                color: #333;
            }
            QPushButton:hover { background: rgba(230,230,230,200); }
        """)
        self.setting_btn.clicked.connect(self.show_settings)
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setFixedSize(36, 36)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,180);
                border: 1px solid rgba(200,200,200,150);
                border-radius: 18px;
                font-size: 16px;
                color: #333;
            }
            QPushButton:hover { background: rgba(255,120,120,180); }
        """)
        self.close_btn.clicked.connect(self.close_app)

        # 根据配置创建子组件（内部会将按钮重新置顶定位）
        self.rebuild_widgets()

    def load_config(self):
        default = {"auto_start": False, "enable_todo": True, "enable_english": True}
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return default
        return default

    def save_config(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def rebuild_widgets(self):
        """根据当前配置重建子组件"""
        # 清除旧组件
        if self.todo_widget:
            self.layout.removeWidget(self.todo_widget)
            self.todo_widget.deleteLater()
            self.todo_widget = None
        if self.english_widget:
            self.layout.removeWidget(self.english_widget)
            self.english_widget.deleteLater()
            self.english_widget = None

        # 计算总高度
        total_height = 0

        # 添加待办
        if self.config.get("enable_todo", True):
            self.todo_widget = TodoWidget(self)
            # 可以设置固定高度，也可以不设，让其根据内容撑开，但我们希望上下比例固定
            self.todo_widget.setFixedHeight(800)  # 可配置
            self.layout.addWidget(self.todo_widget)
            total_height += 800
        # 添加英语
        if self.config.get("enable_english", True):
            self.english_widget = EnglishWidget(self)
            self.english_widget.setFixedHeight(400)
            self.layout.addWidget(self.english_widget)
            total_height += 400

        # 调整窗口总高度（加上边距）
        self.setFixedSize(600, total_height + 20)  # 上下边距各10

        # 悬浮按钮定位到右上角并置顶（新组件创建在后，必须重新 raise）
        self.reposition_corner_buttons()
        self.setting_btn.raise_()
        self.close_btn.raise_()

    def reposition_corner_buttons(self):
        m = 14
        x = self.width() - m
        self.close_btn.move(x - self.close_btn.width(), m)
        self.setting_btn.move(x - self.close_btn.width() - 8 - self.setting_btn.width(), m)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reposition_corner_buttons()

    def show_settings(self):
        try:
            from settings import SettingsDialog
            dlg = SettingsDialog(self, self.config)
            if dlg.exec_():
                # 用户保存后，重新加载配置并重建
                self.config = self.load_config()
                self.rebuild_widgets()
                # 同时更新开机启动（由settings处理）
                notice = getattr(dlg, "autostart_notice", None)
                if notice:
                    QMessageBox.information(self, "已开启自启", notice)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开设置失败：{e}")
        finally:
            # 主窗口是 Qt.Tool + WindowStaysOnBottomHint，模态子对话框关闭后
            # 可能被窗口管理器隐藏且不再重显，这里强制恢复显示，避免看起来像“程序退出”。
            self.show()
            self.raise_()
            self.activateWindow()

    def close_app(self):
        reply = QMessageBox.question(self, "退出确认", "确定退出？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.close()

    def move_to_top_right(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - self.width(), 0)