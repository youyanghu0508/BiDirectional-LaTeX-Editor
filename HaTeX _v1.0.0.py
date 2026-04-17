import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QPushButton
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QUrl, Slot, Signal, QObject
from PySide6.QtWebChannel import QWebChannel

# HTML 模板，内嵌 MathLive 编辑器
# 这里使用了 CDN，实际生产环境建议下载到本地
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <!-- 引入 MathLive -->
    <script type="module" src="https://unpkg.com/mathlive?module"></script>
    <style>
        body { font-family: sans-serif; display: flex; flex-direction: column; height: 100vh; margin: 0; overflow: hidden; }
        #editor-container { flex: 1; display: flex; justify-content: center; align-items: center; background: #f9f9f9; border-bottom: 1px solid #ddd; }
        math-field { font-size: 24px; width: 90%; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        #latex-output { height: 150px; background: #2d2d2d; color: #a9b7c6; padding: 10px; font-family: monospace; border: none; resize: none; outline: none; }
        .label { background: #eee; padding: 5px; font-weight: bold; font-size: 12px; color: #555; }
        .info-label {
    background: #f8f9fa;       /* 背景色稍浅，区分层级 */
    color: #666;               /* 字体颜色稍淡 */
    font-size: 10px;           /* 👈 关键：字体调小为 11px */
    font-weight: normal;       /* 去掉加粗，显得不那么突兀 */
    padding: 4px 15px;         /* 上下内边距调小，让行高更紧凑 */
    border-bottom: 1px solid #eee;
    white-space: nowrap;       /* 防止文字换行 (可选) */
    overflow: hidden;
    text-overflow: ellipsis;
}
    </style>
</head>
<body>

    <div class="label">可视化公式编辑区 (类似 Word)</div>
    <div id="editor-container">
        <!-- MathLive 核心组件 -->
        <math-field id="mf" virtual-keyboard-mode="manual">e^{i\pi}+1=0</math-field>
    </div>

    <div class="label">LaTeX 代码区 (可编辑)</div>
    <textarea id="latex-output" spellcheck="false"></textarea>

    <div class="info-label">开发者：中国科学技术大学-25级-少计-胡悠飏<br>邮箱：youyanghu@mail.ustc.edu.cn<br>⚠️BETA版仅供参考，手册见附件，如有漏洞与建议欢迎邮件联系</div>

    <script>
        // 获取元素
        const mf = document.getElementById('mf');
        const latexOutput = document.getElementById('latex-output');

        // 1. 当可视化公式变化时 -> 更新 LaTeX 文本框
        mf.addEventListener('input', () => {
            const latex = mf.getValue();
            latexOutput.value = latex;
            // 通知 Python 数据变了
            if (window.pythonBridge) {
                window.pythonBridge.updateLatex(latex);
            }
        });

        // 2. 当 LaTeX 文本框变化时 -> 更新可视化公式
        latexOutput.addEventListener('input', () => {
            const latex = latexOutput.value;
            mf.setValue(latex);
             // 通知 Python 数据变了
            if (window.pythonBridge) {
                window.pythonBridge.updateLatex(latex);
            }
        });

        // 暴露给 Python 调用的函数：设置公式
        function setMathField(latex) {
            if (mf.getValue() !== latex) {
                mf.setValue(latex);
                latexOutput.value = latex;
            }
        }
        
        // 初始化桥接对象
        window.onload = function() {
            if (window.qt && window.qt.webChannelTransport) {
                new QWebChannel(window.qt.webChannelTransport, function(channel) {
                    window.pythonBridge = channel.objects.bridge;
                    // 初始化时发送一次当前值
                    window.pythonBridge.updateLatex(mf.getValue());
                });
            }
        };
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

class MathEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HaTeX-BETA版 | 开发者：25-少计-胡悠飏")
        self.resize(800, 600)
        

        # 创建桥接对象
        self.bridge = Bridge()
        self.bridge.latexChanged.connect(self.on_latex_changed_from_js)

        # 设置 Web 视图
        self.web_view = QWebEngineView()
        self.web_view.setHtml(HTML_CONTENT, QUrl("qrc:/")) # 使用 qrc 协议防止本地路径问题

        # 建立通信通道
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # 布局：实际上 web_view 已经包含了左右/上下逻辑，这里我们直接把 web_view 放进去
        # 如果你想把 Python 原生的 QTextEdit 放在右边而不是 HTML 里的 textarea，
        # 则需要修改 HTML 去掉 textarea，并用 Python 信号槽去更新 webview 和 原生TextEdit。
        # 但为了性能和双向同步的流畅度，推荐全部在 Web 引擎内完成 UI，Python 只负责逻辑处理。
        
        self.setCentralWidget(self.web_view)

        # 模拟获取初始值
        print("应用启动，等待用户输入...")

    def on_latex_changed_from_js(self, latex_code):
        """接收来自 JS 的 LaTeX 代码"""
        # 在这里你可以做任何事情，比如保存文件、编译 PDF、发送给后端等
        # print(f"Python 接收到 LaTeX: {latex_code}")
        pass

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