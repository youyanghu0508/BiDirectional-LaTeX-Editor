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
        // ========== 新增：LaTeX 矩阵格式化函数 ==========
        function formatMatrix(latexStr) {
            // 匹配所有矩阵环境：\begin{...matrix} ... \end{...matrix}
            const matrixRegex = /\\begin\{([a-zA-Z]*matrix)\}([\s\S]*?)\\end\{\1\}/g;
            
            return latexStr.replace(matrixRegex, (match, envType, content) => {
                // 按 \\ 分割行
                let rows = content.split('\\\\').map(row => row.trim());
                if (rows.length === 0) return match;
                
                // 将每行按 & 分割，并去除首尾空格
                let cells = rows.map(row => row.split('&').map(cell => cell.trim()));
                
                // 计算每列的最大宽度（字符数）
                let colCount = Math.max(...cells.map(row => row.length));
                let colWidths = Array(colCount).fill(0);
                cells.forEach(row => {
                    row.forEach((cell, idx) => {
                        colWidths[idx] = Math.max(colWidths[idx], cell.length);
                    });
                });
                
                // 重新构建对齐后的行
                let alignedRows = cells.map(row => {
                    let paddedCells = row.map((cell, idx) => {
                        // 对于非最后一列，补齐空格到最大宽度
                        if (idx < colCount - 1) {
                            return cell.padEnd(colWidths[idx], ' ');
                        } else {
                            return cell;
                        }
                    });
                    return '  ' + paddedCells.join(' & ') + ' \\\\';
                });
                
                // 重构整个矩阵环境
                return `\\begin{${envType}}\n${alignedRows.join('\n')}\n\\end{${envType}}`;
            });
        }

        // 新增：格式化当前编辑器的内容（双向更新）
        function formatCurrentMatrix() {
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

        // 将函数挂载到 window，方便 Python 调用
        window.formatCurrentMatrix = formatCurrentMatrix;
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