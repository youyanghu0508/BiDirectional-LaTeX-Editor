#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动截图脚本 - 为 README 生成截图
"""

import sys
import os
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QScreen

# 导入主应用
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

screenshot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(screenshot_dir, exist_ok=True)

app = None
main_window = None
screenshot_index = 0

def take_screenshot(filename):
    """截取当前窗口截图"""
    global screenshot_index
    screenshot_index += 1
    
    # 等待渲染
    QTimer.singleShot(500, lambda: _do_screenshot(filename, screenshot_index))

def _do_screenshot(filename, index):
    """执行截图"""
    screen = QApplication.primaryScreen()
    if screen and main_window:
        # 截取主窗口
        pixmap = screen.grabWindow(main_window.winId())
        filepath = os.path.join(screenshot_dir, filename)
        pixmap.save(filepath, 'PNG')
        print(f"[OK] Screenshot {index}: {filename}")
        
        # 继续下一个截图
        QTimer.singleShot(100, next_screenshot)

def next_screenshot():
    """执行下一个截图任务"""
    global screenshot_index
    
    if screenshot_index == 1:
        # 截图1: 主界面亮色主题（已完成）
        # 输入一个示例公式
        if main_window and hasattr(main_window, 'web_view'):
            js = """
            var mf = document.getElementById('mf');
            if (mf) {
                mf.value = 'E = mc^2';
                mf.dispatchEvent(new Event('input'));
            }
            """
            main_window.web_view.page().runJavaScript(js)
        QTimer.singleShot(1000, lambda: take_screenshot("main-light.png"))
        
    elif screenshot_index == 2:
        # 截图2: 主界面暗色主题
        # 切换暗色主题
        if main_window and hasattr(main_window, 'toggle_theme'):
            main_window.toggle_theme()
        QTimer.singleShot(1000, lambda: take_screenshot("main-dark.png"))
        
    elif screenshot_index == 3:
        # 截图3: 自动补全
        # 切换回亮色主题
        if main_window and hasattr(main_window, 'toggle_theme'):
            main_window.toggle_theme()
        # 在代码区输入 \a 触发自动补全
        if main_window and hasattr(main_window, 'code_editor'):
            main_window.code_editor.setPlainText("\\a")
            # 模拟光标移动到末尾
            cursor = main_window.code_editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            main_window.code_editor.setTextCursor(cursor)
        QTimer.singleShot(1000, lambda: take_screenshot("autocomplete.png"))
        
    elif screenshot_index == 4:
        # 截图4: 矩阵格式化
        # 输入矩阵代码
        if main_window and hasattr(main_window, 'code_editor'):
            matrix_code = r"""\begin{pmatrix}
a & b \\
c & d
\end{pmatrix}"""
            main_window.code_editor.setPlainText(matrix_code)
            # 全选代码
            cursor = main_window.code_editor.textCursor()
            cursor.select(cursor.SelectionType.Document)
            main_window.code_editor.setTextCursor(cursor)
        QTimer.singleShot(1000, lambda: take_screenshot("matrix-format.png"))
        
    elif screenshot_index == 5:
        # 截图5: 收藏管理
        # 清空代码区，输入简单公式
        if main_window and hasattr(main_window, 'code_editor'):
            main_window.code_editor.setPlainText("\\frac{1}{2}")
        # 模拟收藏操作（Ctrl+D）
        if main_window:
            from PySide6.QtGui import QKeyEvent
            from PySide6.QtCore import QEvent
            event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key_D, Qt.KeyboardModifier.ControlModifier)
            QApplication.sendEvent(main_window, event)
        QTimer.singleShot(1500, lambda: take_screenshot("favorites.png"))
        
    elif screenshot_index == 6:
        # 截图6: 历史记录
        # 打开历史记录面板
        if main_window and hasattr(main_window, 'show_history_dialog'):
            main_window.show_history_dialog()
        QTimer.singleShot(1500, lambda: take_screenshot("history.png"))
        
    else:
        # 所有截图完成
        print(f"\n[OK] All screenshots completed! Total: {screenshot_index - 1}")
        print(f"Screenshot save directory: {screenshot_dir}")
        app.quit()

def start_screenshots():
    """开始截图流程"""
    print("Starting screenshots...")
    print(f"Save directory: {screenshot_dir}\n")
    
    # 延迟开始第一个截图
    QTimer.singleShot(2000, lambda: take_screenshot("main-light.png"))

if __name__ == "__main__":
    # 导入主应用类
    from importlib.machinery import SourceFileLoader
    
    # 动态加载主程序
    main_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HaTeX _v1.4.0.py")
    loader = SourceFileLoader("hatex_main", main_file)
    hatex_module = loader.load_module()
    
    MathEditorApp = hatex_module.MathEditorApp
    
    app = QApplication(sys.argv)
    main_window = MathEditorApp()
    main_window.show()
    
    # 开始截图流程
    QTimer.singleShot(2000, start_screenshots)
    
    sys.exit(app.exec())
