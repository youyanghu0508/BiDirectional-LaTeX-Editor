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
    <!-- 引入 MathLive -->
    <link rel="stylesheet" href="mathlive/mathlive-static.css">
    <script src="mathlive/mathlive.min.js"></script>
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
        <math-field 
            id="mf" 
            smart-focus="true"
            smart-mode="true"
            virtual-keyboard-mode="manual">
            e^{i\pi}+1=0
        </math-field>
    </div>

    <div class="label">LaTeX 代码区 (可编辑)</div>
    <textarea id="latex-output" spellcheck="false"></textarea>

    <div class="info-label">开发者：中国科学技术大学-25级-少计-胡悠飏<br>邮箱：youyanghu@mail.ustc.edu.cn<br>⚠️BETA版仅供参考，手册见附件，如有漏洞与建议欢迎邮件联系</div>

    <script>
        // ========== 获取元素 ==========
        const mf = document.getElementById('mf');
        const latexOutput = document.getElementById('latex-output');

        // ========== 配置 MathLive（必须在元素创建后立即执行） ==========
        if (mf) {
            // 方式1：通过 setOptions 配置（推荐）
            mf.setOptions({
                smartMode: true,
                smartFence: true,
                smartSuperscript: true,
            });
            
            // 方式2：添加自定义快捷输入（MathLive 支持的配置）
            // 注意：这是快捷键替换，不是补全菜单
            mf.shortcuts = {
                ...mf.shortcuts,
                '\\R': '\\mathbb{R}',
                '\\N': '\\mathbb{N}',
                '\\Z': '\\mathbb{Z}',
                '\\Q': '\\mathbb{Q}',
                '\\C': '\\mathbb{C}',
            };
        }

        // ========== 原有功能保持不变 ==========
        function debounce(func, wait) {
            let timeout;
            return function(...args) {
                clearTimeout(timeout);
                timeout = setTimeout(() => func(...args), wait);
            };
        }

        function formatMatrix(latexStr) {
            const matrixRegex = /\\begin\{([a-zA-Z]*matrix)\}([\s\S]*?)\\end\{\1\}/g;
            return latexStr.replace(matrixRegex, (match, envType, content) => {
                let rows = content.split('\\\\').map(row => row.trim());
                if (rows.length === 0) return match;
                let cells = rows.map(row => row.split('&').map(cell => cell.trim()));
                let colCount = Math.max(...cells.map(row => row.length));
                let colWidths = Array(colCount).fill(0);
                cells.forEach(row => {
                    row.forEach((cell, idx) => { colWidths[idx] = Math.max(colWidths[idx], cell.length); });
                });
                let alignedRows = cells.map(row => {
                    let paddedCells = row.map((cell, idx) => {
                        if (idx < colCount - 1) return cell.padEnd(colWidths[idx], ' ');
                        else return cell;
                    });
                    return '  ' + paddedCells.join(' & ') + ' \\\\';
                });
                return `\\begin{${envType}}\n${alignedRows.join('\n')}\n\\end{${envType}}`;
            });
        }

        function autoFormatMatrix() {
            let currentLatex = mf.getValue();
            let formatted = formatMatrix(currentLatex);
            if (formatted !== currentLatex) {
                mf.setValue(formatted);
                latexOutput.value = formatted;
                if (window.pythonBridge) {
                    window.pythonBridge.updateLatex(formatted);
                }
            }
        }

        const debouncedAutoFormat = debounce(autoFormatMatrix, 800);

        function onMathFieldInput() {
            const latex = mf.getValue();
            latexOutput.value = latex;
            if (window.pythonBridge) {
                window.pythonBridge.updateLatex(latex);
            }
            debouncedAutoFormat();
        }

        function onLatexOutputInput() {
            const latex = latexOutput.value;
            mf.setValue(latex);
            if (window.pythonBridge) {
                window.pythonBridge.updateLatex(latex);
            }
            debouncedAutoFormat();
        }

        mf.addEventListener('input', onMathFieldInput);
        latexOutput.addEventListener('input', onLatexOutputInput);

        function setMathField(latex) {
            if (mf.getValue() !== latex) {
                mf.setValue(latex);
                latexOutput.value = latex;
            }
        }

        window.onload = function() {
            if (window.qt && window.qt.webChannelTransport) {
                new QWebChannel(window.qt.webChannelTransport, function(channel) {
                    window.pythonBridge = channel.objects.bridge;
                    window.pythonBridge.updateLatex(mf.getValue());
                });
            }
        };

        function formatCurrentMatrix() {
            autoFormatMatrix();
        }
        window.formatCurrentMatrix = formatCurrentMatrix;
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

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Slot, Signal, QObject
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtGui import QAction, QKeySequence   # 新增这一行

class MathEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HaTeX-BETA版 | 开发者：25-少计-胡悠飏")
        self.resize(800, 600)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.bridge = Bridge()
        self.bridge.latexChanged.connect(self.on_latex_changed_from_js)
        
        self.web_view = QWebEngineView()
        self.web_view.setHtml(HTML_CONTENT, QUrl.fromLocalFile(current_dir + "/"))
        
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        
        self.setCentralWidget(self.web_view)
        
        # ---------- 新增：创建菜单栏 ----------
        menubar = self.menuBar()
        tools_menu = menubar.addMenu("工具")
        
        format_action = QAction("格式化矩阵", self)
        format_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        format_action.triggered.connect(self.format_matrix)
        tools_menu.addAction(format_action)
        
        print("应用启动，等待用户输入...")

    def on_latex_changed_from_js(self, latex_code):
        pass

    def set_formula_from_python(self, latex_code):
        js_code = f"setMathField(`{latex_code.replace('`', '\\`')}`);"
        self.web_view.page().runJavaScript(js_code)

    # ---------- 新增：触发 JS 格式化的槽函数 ----------
    def format_matrix(self):
        self.web_view.page().runJavaScript("window.formatCurrentMatrix();")

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