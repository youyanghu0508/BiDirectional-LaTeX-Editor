import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Slot, Signal, QObject
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtGui import QAction, QKeySequence

# HTML 模板，内嵌 MathLive 编辑器
HTML_CONTENT = r"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <!-- 引入 MathLive -->
    <link rel="stylesheet" href="mathlive-static.css">
    <script src="mathlive.min.js"></script>
    <style>
        body { font-family: sans-serif; display: flex; flex-direction: column; height: 100vh; margin: 0; overflow: hidden; }
        #editor-container { flex: 1; display: flex; justify-content: center; align-items: center; background: #f9f9f9; border-bottom: 1px solid #ddd; position: relative; }
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
        /* 自动补全下拉框样式 */
        .autocomplete-suggestions {
            position: absolute;
            background: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            display: none;
            font-family: monospace;
        }
        .autocomplete-suggestions div {
            padding: 8px 12px;
            cursor: pointer;
            font-family: monospace;
            font-size: 14px;
        }
        .autocomplete-suggestions div:hover,
        .autocomplete-suggestions div.selected {
            background: #e3f2fd;
        }
        .suggestion-command { color: #d73a49; font-weight: bold; }
        .suggestion-desc { color: #666; font-size: 12px; margin-left: 10px; }
    </style>
</head>
<body>

    <div class="label">可视化公式编辑区</div>
    <div id="editor-container">
        <math-field 
            id="mf" 
            smart-focus="true"
            smart-mode="true"
            virtual-keyboard-mode="manual">
            e^{i\pi}+1=0
        </math-field>
        <div id="autocomplete" class="autocomplete-suggestions"></div>
    </div>

    <div class="label">LaTeX 代码区 (可编辑) - 支持自动补全，按 Tab 或 Enter 选择</div>
    <textarea id="latex-output" spellcheck="false"></textarea>

    <div class="info-label">开发者：中国科学技术大学-25级-少计-胡悠飏<br>邮箱：youyanghu@mail.ustc.edu.cn<br>⚠️BETA版仅供参考，手册见附件，如有漏洞与建议欢迎邮件联系</div>

    <script>
        // ========== 获取元素 ==========
        const mf = document.getElementById('mf');
        const latexOutput = document.getElementById('latex-output');
        const autocompleteDiv = document.getElementById('autocomplete');

        // ========== 自动补全词库 ==========
        // 注意：在 JavaScript 字符串中，反斜杠必须写成 \\ 才能表示一个字面反斜杠
        const latexCompletions = [
            { trigger: "frac", command: "\\frac{}{}", description: "分数", cursorOffset: 6 },
            { trigger: "sqrt", command: "\\sqrt{}", description: "平方根", cursorOffset: 6 },
            { trigger: "sqrtn", command: "\\sqrt[]{}", description: "n次根号", cursorOffset: 7 },
            { trigger: "int", command: "\\int_{}^{}", description: "定积分", cursorOffset: 6 },
            { trigger: "oint", command: "\\oint_{}^{}", description: "环路积分", cursorOffset: 7 },
            { trigger: "sum", command: "\\sum_{}^{}", description: "求和", cursorOffset: 6 },
            { trigger: "prod", command: "\\prod_{}^{}", description: "求积", cursorOffset: 7 },
            { trigger: "lim", command: "\\lim_{}", description: "极限", cursorOffset: 6 },
            { trigger: "infty", command: "\\infty", description: "无穷大", cursorOffset: 0 },
            { trigger: "alpha", command: "\\alpha", description: "希腊字母α", cursorOffset: 0 },
            { trigger: "beta", command: "\\beta", description: "希腊字母β", cursorOffset: 0 },
            { trigger: "gamma", command: "\\gamma", description: "希腊字母γ", cursorOffset: 0 },
            { trigger: "delta", command: "\\delta", description: "希腊字母δ", cursorOffset: 0 },
            { trigger: "theta", command: "\\theta", description: "希腊字母θ", cursorOffset: 0 },
            { trigger: "pi", command: "\\pi", description: "圆周率π", cursorOffset: 0 },
            { trigger: "sigma", command: "\\sigma", description: "希腊字母σ", cursorOffset: 0 },
            { trigger: "omega", command: "\\omega", description: "希腊字母ω", cursorOffset: 0 },
            { trigger: "rightarrow", command: "\\rightarrow", description: "右箭头", cursorOffset: 0 },
            { trigger: "leftarrow", command: "\\leftarrow", description: "左箭头", cursorOffset: 0 },
            { trigger: "Rightarrow", command: "\\Rightarrow", description: "右双箭头", cursorOffset: 0 },
            { trigger: "Leftarrow", command: "\\Leftarrow", description: "左双箭头", cursorOffset: 0 },
            { trigger: "cdot", command: "\\cdot", description: "点乘", cursorOffset: 0 },
            { trigger: "times", command: "\\times", description: "叉乘", cursorOffset: 0 },
            { trigger: "pm", command: "\\pm", description: "正负号", cursorOffset: 0 },
            { trigger: "mp", command: "\\mp", description: "负正号", cursorOffset: 0 },
            { trigger: "le", command: "\\le", description: "小于等于", cursorOffset: 0 },
            { trigger: "ge", command: "\\ge", description: "大于等于", cursorOffset: 0 },
            { trigger: "ne", command: "\\ne", description: "不等于", cursorOffset: 0 },
            { trigger: "approx", command: "\\approx", description: "约等于", cursorOffset: 0 },
            { trigger: "partial", command: "\\partial", description: "偏导数", cursorOffset: 0 },
            { trigger: "nabla", command: "\\nabla", description: "梯度算子", cursorOffset: 0 },
            { trigger: "forall", command: "\\forall", description: "任意", cursorOffset: 0 },
            { trigger: "exists", command: "\\exists", description: "存在", cursorOffset: 0 },
            { trigger: "in", command: "\\in", description: "属于", cursorOffset: 0 },
            { trigger: "subset", command: "\\subset", description: "子集", cursorOffset: 0 },
            { trigger: "cup", command: "\\cup", description: "并集", cursorOffset: 0 },
            { trigger: "cap", command: "\\cap", description: "交集", cursorOffset: 0 },
            { trigger: "sin", command: "\\sin", description: "正弦", cursorOffset: 0 },
            { trigger: "cos", command: "\\cos", description: "余弦", cursorOffset: 0 },
            { trigger: "tan", command: "\\tan", description: "正切", cursorOffset: 0 },
            { trigger: "log", command: "\\log", description: "对数", cursorOffset: 0 },
            { trigger: "ln", command: "\\ln", description: "自然对数", cursorOffset: 0 },
            { trigger: "exp", command: "\\exp", description: "指数函数", cursorOffset: 0 },
            { trigger: "matrix", command: "\\begin{pmatrix}\n    a & b \\\\\n    c & d\n\\end{pmatrix}", description: "矩阵(pmatrix)", cursorOffset: 0 },
            { trigger: "bmatrix", command: "\\begin{bmatrix}\n    a & b \\\\\n    c & d\n\\end{bmatrix}", description: "矩阵(bmatrix)", cursorOffset: 0 },
            { trigger: "cases", command: "\\begin{cases}\n    a & \\text{if } x>0 \\\\\n    b & \\text{otherwise}\n\\end{cases}", description: "分段函数", cursorOffset: 0 }
        ];

        // 自动补全状态
        let currentSuggestions = [];
        let selectedIndex = -1;
        let currentTriggerWord = "";

        // ========== 配置 MathLive ==========
        if (mf) {
            mf.setOptions({
                smartMode: true,
                smartFence: true,
                smartSuperscript: true,
            });
            
            mf.shortcuts = {
                ...mf.shortcuts,
                '\\R': '\\mathbb{R}',
                '\\N': '\\mathbb{N}',
                '\\Z': '\\mathbb{Z}',
                '\\Q': '\\mathbb{Q}',
                '\\C': '\\mathbb{C}',
            };
        }

        // ========== 辅助函数 ==========
        function debounce(func, wait) {
            let timeout;
            return function(...args) {
                clearTimeout(timeout);
                timeout = setTimeout(() => func(...args), wait);
            };
        }

        // 隐藏自动补全框
        function hideAutocomplete() {
            autocompleteDiv.style.display = 'none';
            currentSuggestions = [];
            selectedIndex = -1;
            currentTriggerWord = "";
        }

        // 显示自动补全框
        function showAutocomplete(suggestions, triggerWord) {
            if (!suggestions.length) {
                hideAutocomplete();
                return;
            }
            
            currentSuggestions = suggestions;
            currentTriggerWord = triggerWord;
            selectedIndex = 0;
            
            // 渲染建议列表
            autocompleteDiv.innerHTML = '';
            suggestions.forEach((item, idx) => {
                const div = document.createElement('div');
                if (idx === 0) div.classList.add('selected');
                div.innerHTML = `<span class="suggestion-command">${item.trigger}</span><span class="suggestion-desc"> → ${item.description}</span>`;
                div.onclick = () => applyCompletion(item);
                div.onmouseenter = () => {
                    selectedIndex = idx;
                    updateSelectedStyle();
                };
                autocompleteDiv.appendChild(div);
            });
            
            // 定位到光标位置
            autocompleteDiv.style.display = 'block';
            
            // 定位到 textarea 光标位置
            const rect = latexOutput.getBoundingClientRect();
            const cursorPos = latexOutput.selectionStart;
            const textBeforeCursor = latexOutput.value.substring(0, cursorPos);
            const lines = textBeforeCursor.split('\n');
            const lineHeight = parseFloat(getComputedStyle(latexOutput).lineHeight);
            const lineCount = lines.length - 1;
            
            autocompleteDiv.style.position = 'absolute';
            autocompleteDiv.style.left = rect.left + 'px';
            autocompleteDiv.style.top = (rect.top + (lineCount + 1) * lineHeight) + 'px';
            autocompleteDiv.style.width = '300px';
        }

        // 更新选中项的样式
        function updateSelectedStyle() {
            const items = autocompleteDiv.children;
            for (let i = 0; i < items.length; i++) {
                if (i === selectedIndex) {
                    items[i].classList.add('selected');
                } else {
                    items[i].classList.remove('selected');
                }
            }
        }

        // ========== 修复：应用补全 - 只替换最后一个反斜杠及其后的字母 ==========
        function applyCompletion(item) {
            const textarea = latexOutput;
            const cursorPos = textarea.selectionStart;
            const text = textarea.value;
            
            // 从光标位置向前查找，找到最后一个反斜杠的位置
            let lastBackslashPos = -1;
            let searchPos = cursorPos - 1;
            
            // 先找最后一个反斜杠（只找最近的一个）
            while (searchPos >= 0) {
                if (text[searchPos] === '\\') {
                    lastBackslashPos = searchPos;
                    break;
                }
                // 如果遇到字母，继续往前
                if (/[a-zA-Z]/.test(text[searchPos])) {
                    searchPos--;
                    continue;
                }
                // 遇到其他字符，停止
                break;
            }
            
            let wordStart = cursorPos;
            
            if (lastBackslashPos !== -1) {
                // 找到了反斜杠，从反斜杠位置开始替换
                wordStart = lastBackslashPos;
            } else {
                // 没有反斜杠，只查找连续的字母
                searchPos = cursorPos - 1;
                while (searchPos >= 0 && /[a-zA-Z]/.test(text[searchPos])) {
                    wordStart = searchPos;
                    searchPos--;
                }
            }
            
            // 删除原有单词，插入补全命令
            const before = text.substring(0, wordStart);
            const after = text.substring(cursorPos);
            const newValue = before + item.command + after;
            
            textarea.value = newValue;
            
            // 设置光标位置
            let newCursorPos = wordStart + item.command.length;
            if (item.cursorOffset > 0) {
                newCursorPos = wordStart + item.cursorOffset;
            }
            textarea.setSelectionRange(newCursorPos, newCursorPos);
            
            // 同步到 math-field
            mf.setValue(newValue);
            if (window.pythonBridge) {
                window.pythonBridge.updateLatex(newValue);
            }
            
            hideAutocomplete();
            textarea.focus();
        }

        // ========== 修复：获取光标前的触发词（只检测最后一个反斜杠） ==========
        function getTriggerWordAtCursor(text, cursorPos) {
            let searchPos = cursorPos - 1;
            let letters = [];
            let hasBackslash = false;
            
            // 先找最后一个反斜杠（只找最近的一个）
            while (searchPos >= 0) {
                const ch = text[searchPos];
                if (ch === '\\') {
                    hasBackslash = true;
                    // 找到了反斜杠，停止继续向前（不往前找更早的反斜杠）
                    break;
                } else if (/[a-zA-Z]/.test(ch)) {
                    letters.unshift(ch);
                    searchPos--;
                } else {
                    break;
                }
            }
            
            const pureTrigger = letters.join('');
            return {
                pureTrigger: pureTrigger,
                hasBackslash: hasBackslash,
                fullLength: (hasBackslash ? 1 : 0) + pureTrigger.length
            };
        }

        // 检查并显示补全建议
        function checkAndShowCompletions() {
            const cursorPos = latexOutput.selectionStart;
            const text = latexOutput.value;
            const triggerInfo = getTriggerWordAtCursor(text, cursorPos);
            
            // 至少输入1个字母才触发补全
            if (triggerInfo.pureTrigger.length >= 1) {
                const suggestions = latexCompletions.filter(item => 
                    item.trigger.toLowerCase().startsWith(triggerInfo.pureTrigger.toLowerCase())
                );
                
                if (suggestions.length > 0) {
                    showAutocomplete(suggestions, triggerInfo.pureTrigger);
                    return;
                }
            }
            
            hideAutocomplete();
        }

        // 格式化矩阵
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
        const debouncedCheckCompletions = debounce(checkAndShowCompletions, 150);

        function onMathFieldInput() {
            const latex = mf.getValue();
            latexOutput.value = latex;
            if (window.pythonBridge) {
                window.pythonBridge.updateLatex(latex);
            }
            debouncedAutoFormat();
        }

        // 处理 textarea 输入
        function onLatexOutputInput(e) {
            const latex = latexOutput.value;
            const cursorPos = latexOutput.selectionStart;
            
            // 自动补全括号
            if (e.inputType === 'insertText' && e.data) {
                let needsComplete = false;
                let completeChar = '';
                
                if (e.data === '{') {
                    needsComplete = true;
                    completeChar = '}';
                } else if (e.data === '(') {
                    needsComplete = true;
                    completeChar = ')';
                } else if (e.data === '[') {
                    needsComplete = true;
                    completeChar = ']';
                }
                
                if (needsComplete) {
                    const beforeCursor = latex.slice(0, cursorPos);
                    const afterCursor = latex.slice(cursorPos);
                    if (afterCursor[0] !== completeChar) {
                        latexOutput.value = beforeCursor + completeChar + afterCursor;
                        latexOutput.setSelectionRange(cursorPos, cursorPos);
                        mf.setValue(latexOutput.value);
                        debouncedCheckCompletions();
                        return;
                    }
                }
            }
            
            mf.setValue(latex);
            if (window.pythonBridge) {
                window.pythonBridge.updateLatex(latex);
            }
            debouncedAutoFormat();
            debouncedCheckCompletions();
        }

        // 处理键盘事件
        function onLatexOutputKeydown(e) {
            if (autocompleteDiv.style.display === 'block' && currentSuggestions.length > 0) {
                if (e.key === 'Tab' || e.key === 'Enter') {
                    e.preventDefault();
                    if (selectedIndex >= 0 && currentSuggestions[selectedIndex]) {
                        applyCompletion(currentSuggestions[selectedIndex]);
                    }
                    return;
                } else if (e.key === 'Escape') {
                    e.preventDefault();
                    hideAutocomplete();
                    return;
                } else if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    selectedIndex = Math.min(selectedIndex + 1, currentSuggestions.length - 1);
                    updateSelectedStyle();
                    return;
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    selectedIndex = Math.max(selectedIndex - 1, 0);
                    updateSelectedStyle();
                    return;
                }
            }
            
            // 退格键时延迟重新检查补全
            if (e.key === 'Backspace') {
                setTimeout(() => debouncedCheckCompletions(), 50);
            }
        }

        // 光标移动时隐藏补全
        function onLatexOutputClickOrMove() {
            hideAutocomplete();
        }

        mf.addEventListener('input', onMathFieldInput);
        latexOutput.addEventListener('input', onLatexOutputInput);
        latexOutput.addEventListener('keydown', onLatexOutputKeydown);
        latexOutput.addEventListener('click', onLatexOutputClickOrMove);
        latexOutput.addEventListener('keyup', function(e) {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                hideAutocomplete();
            }
        });

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
        window.setMathField = setMathField;
    </script>
</body>
</html>
"""

class Bridge(QObject):
    """Python 与 JavaScript 通信的桥梁"""
    latexChanged = Signal(str)

    def __init__(self):
        super().__init__()

    @Slot(str)
    def updateLatex(self, latex):
        self.latexChanged.emit(latex)

    @Slot(str)
    def setFormula(self, latex):
        pass


class MathEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HaTeX-BETA版 | 开发者：25-少计-胡悠飏")
        self.resize(800, 600)
        
        # 处理打包后的路径
        if getattr(sys, 'frozen', False):
            # 打包后的 exe 运行
            base_dir = sys._MEIPASS
        else:
            # 正常 Python 脚本运行
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        mathlive_path = os.path.join(base_dir, 'mathlive').replace('\\', '/')
        
        self.bridge = Bridge()
        self.bridge.latexChanged.connect(self.on_latex_changed_from_js)
        
        # 必须先创建 web_view
        self.web_view = QWebEngineView()
        self.web_view.setHtml(HTML_CONTENT, QUrl.fromLocalFile(mathlive_path + "/"))
        
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        
        self.setCentralWidget(self.web_view)
        
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
        escaped = latex_code.replace('\\', '\\\\').replace('`', '\\`')
        js_code = f"setMathField(`{escaped}`);"
        self.web_view.page().runJavaScript(js_code)

    def format_matrix(self):
        self.web_view.page().runJavaScript("window.formatCurrentMatrix();")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MathEditorApp()
    window.show()
    sys.exit(app.exec())