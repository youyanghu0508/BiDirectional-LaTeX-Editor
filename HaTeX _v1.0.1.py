import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QPushButton
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QUrl, Slot, Signal, QObject
from PySide6.QtWebChannel import QWebChannel

# HTML 模板，内嵌 MathLive 编辑器
# 这里使用了 CDN，实际生产环境建议下载到本地
HTML_CONTENT = r"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="https://unpkg.com/mathlive@0.94.0/dist/mathlive-static.css">
    <style>
        body { font-family: sans-serif; display: flex; flex-direction: column; height: 100vh; margin: 0; overflow: hidden; }
        #editor-container { flex: 1; display: flex; justify-content: center; align-items: center; background: #f9f9f9; border-bottom: 1px solid #ddd; }
        math-field { font-size: 24px; width: 90%; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        #latex-output { height: 150px; background: #2d2d2d; color: #a9b7c6; padding: 10px; font-family: monospace; border: none; resize: none; outline: none; }
        .label { background: #eee; padding: 5px; font-weight: bold; font-size: 12px; color: #555; }
        .info-label {
    background: #f8f9fa;       
    color: #666;               
    font-size: 10px;           
    font-weight: normal;       
    padding: 4px 15px;         
    border-bottom: 1px solid #eee;
    white-space: nowrap;       
    overflow: hidden;
    text-overflow: ellipsis;
}
    </style>
</head>
<body>
    <div class="label">可视化公式编辑区 (类似 Word)</div>
    <div id="editor-container">
        <math-field id="mf" virtual-keyboard-mode="manual">e^{i\pi}+1=0</math-field>
    </div>

    <div class="label">LaTeX 代码区 (可编辑)</div>
    <textarea id="latex-output" spellcheck="false"></textarea>

    <div class="info-label">开发者：中国科学技术大学-25级-少计-胡悠飏<br>邮箱：youyanghu@mail.ustc.edu.cn<br>⚠️BETA版仅供参考，手册见附件，如有漏洞与建议欢迎邮件联系</div>

    <script src="https://unpkg.com/mathlive@0.94.0/dist/mathlive.min.js"></script>
    <script>
        // 获取元素
        const mf = document.getElementById('mf');
        const latexOutput = document.getElementById('latex-output');

        // 1. 当可视化公式变化时 -> 更新 LaTeX 文本框
        mf.addEventListener('input', () => {
            const latex = mf.getValue();
            latexOutput.value = latex;
            console.log('JS: Math field changed, sending to Python:', latex);
            // 通知 Python 数据变了
            if (window.pythonBridge) {
                window.pythonBridge.updateLatex(latex);
            } else {
                console.log('JS: pythonBridge not available yet');
            }
        });

        // 2. 当 LaTeX 文本框变化时 -> 更新可视化公式
        latexOutput.addEventListener('input', () => {
            const latex = latexOutput.value;
            console.log('JS: LaTeX output changed:', latex);
            mf.setValue(latex);
            // 通知 Python 数据变了
            if (window.pythonBridge) {
                window.pythonBridge.updateLatex(latex);
            }
        });

        // 暴露给 Python 调用的函数：设置公式
        function setMathField(latex) {
            console.log('JS: Setting math field to:', latex);
            if (mf.getValue() !== latex) {
                mf.setValue(latex);
                latexOutput.value = latex;
            }
        }
        
        // 等待 WebChannel 准备好后再初始化
        if (typeof QWebChannel !== 'undefined') {
            console.log('JS: QWebChannel available, initializing...');
            new QWebChannel(window.qt.webChannelTransport, function(channel) {
                window.pythonBridge = channel.objects.bridge;
                console.log('JS: Bridge established, sending initial value');
                // 初始化时发送一次当前值
                window.pythonBridge.updateLatex(mf.getValue());
            });
        } else {
            console.log('JS: Waiting for QWebChannel...');
            // 如果 QWebChannel 还没准备好，延迟一段时间再尝试
            setTimeout(function() {
                if (typeof QWebChannel !== 'undefined') {
                    new QWebChannel(window.qt.webChannelTransport, function(channel) {
                        window.pythonBridge = channel.objects.bridge;
                        window.pythonBridge.updateLatex(mf.getValue());
                    });
                } else {
                    console.error('JS: QWebChannel still not available!');
                }
            }, 1000);
        }
    </script>
</body>
</html>
"""

class Bridge(QObject):
    """Python 与 JavaScript 通信的桥梁"""
    # 定义一个信号，当 JS 端 LaTeX 变化时触发，通知 Python
    latexChanged = Signal(str)

    def __init__(self):
        super().__init__()

    @Slot(str)
    def updateLatex(self, latex):
        """JS 调用此方法通知 Python LaTeX 已更新"""
        self.latexChanged.emit(latex)

    @Slot(str)
    def setFormula(self, latex):
        """Python 调用此方法（虽然本例主要靠 JS 内部同步，但预留接口）"""
        pass 

import os

class MathEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HaTeX-BETA版 | 开发者：25-少计-胡悠飏")
        self.resize(800, 600)
        
        # 创建桥接对象
        self.bridge = Bridge()
        self.bridge.latexChanged.connect(self.on_latex_changed_from_js)
        
        # 设置Web视图
        self.web_view = QWebEngineView()
        self.web_view.setHtml(HTML_CONTENT)
        
        # 建立通信通道 - 这一步必须在页面加载完成前设置
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        
        self.setCentralWidget(self.web_view)

    

    
    def format_latex(self, latex_code):
        """格式化LaTeX代码，让矩阵等结构更清晰"""
        try:
            print(f"[DEBUG] 开始格式化LaTeX代码: {repr(latex_code[:100])}...")  # 调试信息
            
            import re
            
            def format_matrix(match):
                matrix_type = match.group(1)
                content = match.group(2)
                
                print(f"[DEBUG] 匹配到矩阵类型: {matrix_type}, 内容: {repr(content)}")  # 调试信息
                
                # 按行分割
                lines = re.split(r'\\\\', content)
                print(f"[DEBUG] 分割后的行: {lines}")  # 调试信息
                
                # 清理每一行
                formatted_lines = []
                for line in lines:
                    clean_line = line.strip()
                    if clean_line:  # 如果行不为空
                        formatted_lines.append('  ' + clean_line)
                
                print(f"[DEBUG] 清理后的行: {formatted_lines}")  # 调试信息
                
                # 组装最终结果，每行独立显示
                result = f'\\begin{{{matrix_type}}}\n' + ' \\\\\n'.join(formatted_lines) + f'\n\\end{{{matrix_type}}}'
                print(f"[DEBUG] 矩阵格式化结果: {repr(result)}")  # 调试信息
                return result

            # 更宽松的正则表达式，匹配各种矩阵类型
            matrix_pattern = r'(\\begin\{([a-z]*matrix)\})(.*?)(\\end\{\2\})'
            
            def replace_func(match):
                full_begin = match.group(1)  # 完整的 begin 部分
                matrix_type = match.group(2)  # 矩阵类型
                content = match.group(3)      # 矩阵内容
                full_end = match.group(4)     # 完整的 end 部分
                
                print(f"[DEBUG] 替换函数 - 类型: {matrix_type}, 内容: {repr(content)}")  # 调试信息
                
                # 按行分割
                lines = re.split(r'\\\\', content)
                
                # 清理每一行
                formatted_lines = []
                for line in lines:
                    clean_line = line.strip()
                    if clean_line:
                        formatted_lines.append('  ' + clean_line)
                
                # 重新构建格式化的矩阵
                result = f'\\begin{{{matrix_type}}}\n' + ' \\\\\n'.join(formatted_lines) + f'\n\\end{{{matrix_type}}}'
                print(f"[DEBUG] 重构结果: {repr(result)}")  # 调试信息
                return result

            formatted = re.sub(matrix_pattern, replace_func, latex_code, flags=re.DOTALL)
            print(f"[DEBUG] 最终格式化结果: {repr(formatted)}")  # 调试信息
            return formatted
        except Exception as e:
            print(f"[ERROR] 格式化过程中发生错误: {e}")  # 错误信息
            import traceback
            traceback.print_exc()  # 打印详细错误信息
            return latex_code  # 返回原始内容以防出错

    def on_latex_changed_from_js(self, latex_code):
        """接收来自JS的LaTeX代码，格式化后显示"""
        print(f"[DEBUG] 收到来自JS的LaTeX代码: {repr(latex_code[:200])}...")
        
        # 格式化LaTeX代码
        formatted_latex = self.format_latex(latex_code)
        
        # 如果你想在Python端打印或保存
        print(f"[DEBUG] 最终输出的格式化LaTeX:\n{formatted_latex}")

    def set_formula_from_python(self, latex_code):
        """从 Python 代码强制设置公式"""
        js_code = f"setMathField(`{latex_code.replace('`', '\\`')}`);"
        self.web_view.page().runJavaScript(js_code)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 启用 WebGL 硬件加速（可选，提升渲染性能）
    # QQuickWindow.setSceneGraphBackend('software') 

    window = MathEditorApp()
    window.show()
    
    # 测试：2秒后自动修改公式
    # import time
    # time.sleep(2) 
    # window.set_formula_from_python(r"\int_{0}^{\infty} e^{-x^2} dx")

    sys.exit(app.exec())