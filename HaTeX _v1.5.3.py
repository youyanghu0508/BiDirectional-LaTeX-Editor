import sys
import os
import json
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Slot, Signal, QObject, QTimer
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtGui import QAction, QKeySequence, QPixmap, QDragEnterEvent, QDropEvent
from PySide6.QtWebEngineCore import QWebEngineSettings

def get_bundle_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

HISTORY_FILE = "hatex_history.json"
FAVORITES_FILE = "hatex_favorites.json"
CONFIG_FILE = "hatex_config.json"
MAX_HISTORY = 50

TRANSLATIONS = {
    "zh": {
        "window_title": "HaTeX v1.5.3 | 开发者：25-少计-胡悠飏",
        "menu_file": "文件",
        "menu_tools": "工具",
        "menu_view": "视图",
        "menu_favorites": "收藏",
        "menu_history": "历史",
        "menu_language": "语言",
        "action_copy_latex": "复制 LaTeX 代码",
        "action_copy_image": "复制为图片 (PNG)",
        "action_export_png": "导出为 PNG...",
        "action_export_svg": "导出为 SVG (MathML)...",
        "action_open_tex": "打开 .tex 文件...",
        "action_save_tex": "保存为 .tex 文件...",
        "action_format_matrix": "格式化矩阵",
        "action_zoom_in": "放大",
        "action_zoom_out": "缩小",
        "action_zoom_reset": "重置缩放",
        "action_dark_mode": "暗色主题",
        "action_add_favorite": "收藏当前公式",
        "dialog_export_png": "导出 PNG",
        "dialog_export_mathml": "导出 MathML",
        "dialog_open_tex": "打开 .tex 文件",
        "dialog_save_tex": "保存 .tex 文件",
        "dialog_open_failed": "打开失败",
        "filter_png": "PNG 文件 (*.png)",
        "filter_xml": "XML 文件 (*.xml)",
        "filter_tex": "TeX 文件 (*.tex);;所有文件 (*)",
        "history_empty": "(空)",
        "startup_msg": "HaTeX v1.5.3 启动",
    },
    "en": {
        "window_title": "HaTeX v1.5.3 | Developer: SCGI 2025 Hu Youyang",
        "menu_file": "File",
        "menu_tools": "Tools",
        "menu_view": "View",
        "menu_favorites": "Favorites",
        "menu_history": "History",
        "menu_language": "Language",
        "action_copy_latex": "Copy LaTeX Code",
        "action_copy_image": "Copy as Image (PNG)",
        "action_export_png": "Export as PNG...",
        "action_export_svg": "Export as SVG (MathML)...",
        "action_open_tex": "Open .tex File...",
        "action_save_tex": "Save as .tex File...",
        "action_format_matrix": "Format Matrix",
        "action_zoom_in": "Zoom In",
        "action_zoom_out": "Zoom Out",
        "action_zoom_reset": "Reset Zoom",
        "action_dark_mode": "Dark Theme",
        "action_add_favorite": "Favorite Current Formula",
        "dialog_export_png": "Export PNG",
        "dialog_export_mathml": "Export MathML",
        "dialog_open_tex": "Open .tex File",
        "dialog_save_tex": "Save as .tex File",
        "dialog_open_failed": "Open Failed",
        "filter_png": "PNG Files (*.png)",
        "filter_xml": "XML Files (*.xml)",
        "filter_tex": "TeX Files (*.tex);;All Files (*)",
        "history_empty": "(Empty)",
        "startup_msg": "HaTeX v1.5.3 started",
    }
}

HTML_CONTENT = r"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="mathlive/mathlive-static.css">
    <script src="mathlive/mathlive.min.js"></script>
    <style>
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f9f9f9;
            --bg-label: #eeeeee;
            --bg-info: #f8f9fa;
            --bg-code: #2d2d2d;
            --text-primary: #333333;
            --text-secondary: #555555;
            --text-info: #666666;
            --text-code: #a9b7c6;
            --border-color: #dddddd;
            --shadow-color: rgba(0,0,0,0.1);
            --autocomplete-bg: white;
            --autocomplete-hover: #e3f2fd;
        }
        body.dark-mode {
            --bg-primary: #1e1e1e;
            --bg-secondary: #252526;
            --bg-label: #333333;
            --bg-info: #2d2d2d;
            --bg-code: #1a1a2e;
            --text-primary: #d4d4d4;
            --text-secondary: #aaaaaa;
            --text-info: #888888;
            --text-code: #ce9178;
            --border-color: #404040;
            --shadow-color: rgba(0,0,0,0.3);
            --autocomplete-bg: #2d2d2d;
            --autocomplete-hover: #3e3e4e;
        }
        body {
            font-family: sans-serif;
            display: flex;
            flex-direction: column;
            height: 100vh;
            margin: 0;
            overflow: hidden;
            background: var(--bg-primary);
            color: var(--text-primary);
            transition: background 0.3s, color 0.3s;
        }
        #editor-container {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            position: relative;
        }
        math-field {
            font-size: 24px;
            width: 90%;
            padding: 20px;
            background: var(--bg-primary);
            border-radius: 8px;
            box-shadow: 0 2px 5px var(--shadow-color);
            color: var(--text-primary);
            outline: none;
            border: 2px solid transparent;
            transition: border-color 0.3s;
        }
        math-field:focus {
            border-color: #4a90e2;
        }
        .code-container {
            height: 150px;
            position: relative;
            background: var(--bg-code);
        }
        #code-highlight {
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            padding: 10px;
            font-family: monospace;
            font-size: 13px;
            line-height: 1.5;
            color: var(--text-code);
            overflow: hidden;
            white-space: pre-wrap;
            word-wrap: break-word;
            margin: 0;
            border: none;
            pointer-events: none;
        }
        #latex-output {
            position: absolute;
            top: 0; left: 0;
            height: 100%;
            width: 100%;
            background: transparent;
            color: transparent;
            caret-color: var(--text-code);
            padding: 10px;
            font-family: monospace;
            font-size: 13px;
            line-height: 1.5;
            border: none;
            resize: none;
            outline: none;
            box-sizing: border-box;
            overflow-y: auto;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            z-index: 1;
        }
        .hl-cmd { color: #c586c0; }
        .hl-brace { color: #ffd700; }
        .hl-number { color: #b5cea8; }
        .hl-comment { color: #6a9955; font-style: italic; }
        body.dark-mode .hl-cmd { color: #ce9178; }
        body.dark-mode .hl-brace { color: #daa520; }
        body.dark-mode .hl-number { color: #b5cea8; }
        body.dark-mode .hl-comment { color: #6a9955; }
        .label {
            background: var(--bg-label);
            padding: 5px;
            font-weight: bold;
            font-size: 12px;
            color: var(--text-secondary);
        }
        .label-with-btn {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 5px 8px;
        }
        #btn-copy-latex {
            background: none;
            border: 1px solid var(--border-color);
            border-radius: 3px;
            cursor: pointer;
            font-size: 14px;
            padding: 2px 6px;
            color: var(--text-secondary);
            transition: background 0.2s;
        }
        #btn-copy-latex:hover {
            background: var(--autocomplete-hover);
        }
        .info-label {
            background: var(--bg-info);
            color: var(--text-info);
            font-size: 10px;
            font-weight: normal;
            padding: 4px 15px;
            border-bottom: 1px solid var(--border-color);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .autocomplete-suggestions {
            position: absolute;
            background: var(--autocomplete-bg);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            box-shadow: 0 2px 5px var(--shadow-color);
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
            background: var(--autocomplete-hover);
        }
        .suggestion-command { color: #d73a49; font-weight: bold; }
        .suggestion-desc { color: #666; font-size: 12px; margin-left: 10px; }
        body.dark-mode .suggestion-command { color: #f48771; }
        body.dark-mode .suggestion-desc { color: #aaa; }
        #zoom-indicator {
            position: fixed;
            bottom: 40px;
            right: 20px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
            opacity: 0;
            transition: opacity 0.3s;
            z-index: 9999;
            pointer-events: none;
        }
        #zoom-indicator.visible { opacity: 1; }
    </style>
</head>
<body>

    <div class="label" id="label-editor">可视化公式编辑区</div>
    <div id="editor-container">
        <math-field
            id="mf"
            tabindex="0"
            smart-mode="true">
        </math-field>
        <div id="autocomplete" class="autocomplete-suggestions"></div>
    </div>

    <div class="label label-with-btn" id="label-code">
        <span id="label-code-text">LaTeX 代码区 (可编辑) - 支持自动补全，按 Tab 或 Enter 选择</span>
        <button id="btn-copy-latex" title="复制 LaTeX 代码" type="button" onclick="window.hatexCopyLatex(event)">📋</button>
    </div>
    <div class="code-container">
        <pre id="code-highlight"></pre>
        <textarea id="latex-output" spellcheck="false"></textarea>
    </div>

    <div class="info-label" id="info-label">开发者：中国科学技术大学-25级-少计-胡悠飏<br>邮箱：youyanghu@mail.ustc.edu.cn<br>⚠️v1.5.3版仅供参考，手册见附件，如有漏洞与建议欢迎邮件联系</div>

    <div id="zoom-indicator">100%</div>

    <!-- 独立的复制按钮处理器：不依赖主编辑器脚本成功初始化 -->
    <script>
    (function () {
        window.hatexCopyLatex = function (event) {
            if (event) { event.preventDefault(); event.stopPropagation(); }
            var btn = document.getElementById('btn-copy-latex');
            var mfEl = document.getElementById('mf');
            var sourceEl = document.getElementById('latex-output');
            var latex = '';
            try {
                if (mfEl && typeof mfEl.getValue === 'function') latex = mfEl.getValue('latex') || mfEl.getValue() || '';
            } catch (e) {}
            if (!latex && sourceEl) latex = sourceEl.value || '';
            if (!latex) {
                if (btn) { btn.textContent = '⚠️'; btn.title = '没有可复制的公式'; }
                return;
            }
            function feedback(ok, message) {
                if (!btn) return;
                btn.textContent = ok ? '✅' : '⚠️';
                btn.title = message;
                window.setTimeout(function () {
                    btn.textContent = '📋'; btn.title = '复制 LaTeX 代码';
                }, 1200);
            }
            try {
                if (window.pythonBridge && typeof window.pythonBridge.copyToClipboard === 'function') {
                    window.pythonBridge.copyToClipboard(latex);
                    feedback(true, '已发送到系统剪贴板');
                    return;
                }
            } catch (e) {}
            // Qt WebEngine 中 clipboard API 可能不可用，使用临时文本框兼容复制。
            try {
                var temp = document.createElement('textarea');
                temp.value = latex;
                temp.setAttribute('readonly', '');
                temp.style.position = 'fixed'; temp.style.left = '-10000px'; temp.style.top = '0';
                document.body.appendChild(temp); temp.focus(); temp.select();
                var ok = document.execCommand('copy');
                document.body.removeChild(temp);
                feedback(ok, ok ? '已复制 LaTeX 代码' : '复制失败：请检查页面脚本或剪贴板');
            } catch (e) {
                feedback(false, '复制失败：' + String(e));
            }
        };
    })();
    </script>

    <script>
        const mf = document.getElementById('mf');
        const latexOutput = document.getElementById('latex-output');
        const autocompleteDiv = document.getElementById('autocomplete');
        const zoomIndicator = document.getElementById('zoom-indicator');

        let currentFontSize = 24;
        let isDarkMode = false;

        const latexCompletions = [
            { trigger: "frac", command: "\\frac{}{}", description: "分数", cursorOffset: 6 },
            { trigger: "sqrt", command: "\\sqrt{}", description: "平方根", cursorOffset: 6 },
            { trigger: "sqrtn", command: "\\sqrt[]{}", description: "n次根号", cursorOffset: 8 },
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

        let currentSuggestions = [];
        let selectedIndex = -1;
        let currentTriggerWord = "";
        let isSyncing = false;
        let currentLang = "zh";

        const uiTranslations = {
            zh: {
                label_editor: "可视化公式编辑区",
                label_code: "LaTeX 代码区 (可编辑) - 支持自动补全，按 Tab 或 Enter 选择",
                info_label: "开发者：中国科学技术大学-25级-少计-胡悠飏<br>邮箱：youyanghu@mail.ustc.edu.cn<br>⚠️v1.5.3版仅供参考，手册见附件，如有漏洞与建议欢迎邮件联系"
            },
            en: {
                label_editor: "Visual Formula Editor",
                label_code: "LaTeX Code (Editable) - Autocomplete supported, press Tab or Enter to select",
                info_label: "Developer: USTC SCGI 2025 Hu Youyang<br>Email: youyanghu@mail.ustc.edu.cn<br>⚠️v1.5.2 for reference only. Bugs & suggestions welcome via email"
            }
        };

        function setLanguage(lang) {
            currentLang = lang;
            var t = uiTranslations[lang];
            if (!t) return;
            var el;
            el = document.getElementById('label-editor');
            if (el) el.textContent = t.label_editor;
            el = document.getElementById('label-code-text');
            if (el) el.textContent = t.label_code;
            el = document.getElementById('info-label');
            if (el) el.innerHTML = t.info_label;
            if (window.pythonBridge) window.pythonBridge.saveLanguage(lang);
        }
        window.setLanguage = setLanguage;

        if (mf) {
            mf.setOptions({
                smartMode: true,
                smartFence: true,
                smartSuperscript: true,
                locale: 'zh-CN'
            });
        }

        // ========== 缩放控制 ==========
        document.getElementById('editor-container').addEventListener('wheel', function(e) {
            if (e.ctrlKey) {
                e.preventDefault();
                const delta = e.deltaY > 0 ? -2 : 2;
                currentFontSize = Math.max(12, Math.min(72, currentFontSize + delta));
                mf.style.fontSize = currentFontSize + 'px';
                const pct = Math.round((currentFontSize / 24) * 100);
                zoomIndicator.textContent = pct + '%';
                zoomIndicator.classList.add('visible');
                clearTimeout(zoomIndicator._timeout);
                zoomIndicator._timeout = setTimeout(() => {
                    zoomIndicator.classList.remove('visible');
                }, 1000);
            }
        }, { passive: false });

        function setZoom(size) {
            currentFontSize = Math.max(12, Math.min(72, size));
            mf.style.fontSize = currentFontSize + 'px';
        }

        // ========== 暗色主题 ==========
        function toggleDarkMode(dark) {
            isDarkMode = dark;
            if (dark) {
                document.body.classList.add('dark-mode');
            } else {
                document.body.classList.remove('dark-mode');
            }
        }

        // ========== 辅助函数 ==========
        function debounce(func, wait) {
            let timeout;
            return function(...args) {
                clearTimeout(timeout);
                timeout = setTimeout(() => func(...args), wait);
            };
        }

        // ========== LaTeX 语法高亮 ==========
        function highlightLatex(text) {
            if (!text) return '';
            var html = text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
            html = html.replace(
                /%(.*)/g,
                '<span class="hl-comment">%$1</span>'
            );
            html = html.replace(
                /\\[a-zA-Z@]+|\\[^a-zA-Z@]/g,
                '<span class="hl-cmd">$&</span>'
            );
            html = html.replace(
                /[{}]/g,
                '<span class="hl-brace">$&</span>'
            );
            html = html.replace(
                /(?<![&\w])(\d+\.?\d*)/g,
                '<span class="hl-number">$1</span>'
            );
            return html;
        }

        function updateHighlight() {
            var pre = document.getElementById('code-highlight');
            if (pre) {
                pre.innerHTML = highlightLatex(latexOutput.value) + '\n';
            }
        }

        function hideAutocomplete() {
            autocompleteDiv.style.display = 'none';
            currentSuggestions = [];
            selectedIndex = -1;
            currentTriggerWord = "";
        }

        function showAutocomplete(suggestions, triggerWord) {
            if (!suggestions.length) { hideAutocomplete(); return; }
            currentSuggestions = suggestions;
            currentTriggerWord = triggerWord;
            selectedIndex = 0;
            autocompleteDiv.innerHTML = '';
            suggestions.forEach((item, idx) => {
                const div = document.createElement('div');
                if (idx === 0) div.classList.add('selected');
                div.innerHTML = '<span class="suggestion-command">' + item.trigger + '</span><span class="suggestion-desc"> \u2192 ' + item.description + '</span>';
                div.onclick = () => applyCompletion(item);
                div.onmouseenter = () => { selectedIndex = idx; updateSelectedStyle(); };
                autocompleteDiv.appendChild(div);
            });
            autocompleteDiv.style.display = 'block';
            const rect = latexOutput.getBoundingClientRect();
            const cursorPos = latexOutput.selectionStart;
            const textBeforeCursor = latexOutput.value.substring(0, cursorPos);
            const lines = textBeforeCursor.split('\n');
            const lineHeight = parseFloat(getComputedStyle(latexOutput).lineHeight);
            const lineCount = lines.length - 1;
            const currentLineText = lines[lines.length - 1];
            const charWidth = parseFloat(getComputedStyle(latexOutput).fontSize) * 0.6;
            const paddingLeft = parseFloat(getComputedStyle(latexOutput).paddingLeft);
            const horizontalOffset = paddingLeft + currentLineText.length * charWidth;
            autocompleteDiv.style.position = 'absolute';
            autocompleteDiv.style.left = (rect.left + horizontalOffset) + 'px';
            autocompleteDiv.style.top = (rect.top + (lineCount + 1) * lineHeight) + 'px';
            autocompleteDiv.style.width = '300px';
        }

        function updateSelectedStyle() {
            const items = autocompleteDiv.children;
            for (let i = 0; i < items.length; i++) {
                if (i === selectedIndex) items[i].classList.add('selected');
                else items[i].classList.remove('selected');
            }
        }

        function applyCompletion(item) {
            const textarea = latexOutput;
            const cursorPos = textarea.selectionStart;
            const text = textarea.value;
            let lastBackslashPos = -1;
            let searchPos = cursorPos - 1;
            while (searchPos >= 0) {
                if (text[searchPos] === '\\') { lastBackslashPos = searchPos; break; }
                if (/[a-zA-Z]/.test(text[searchPos])) { searchPos--; continue; }
                break;
            }
            let wordStart = cursorPos;
            if (lastBackslashPos !== -1) {
                wordStart = lastBackslashPos;
            } else {
                searchPos = cursorPos - 1;
                while (searchPos >= 0 && /[a-zA-Z]/.test(text[searchPos])) {
                    wordStart = searchPos; searchPos--;
                }
            }
            const before = text.substring(0, wordStart);
            const after = text.substring(cursorPos);
            const newValue = before + item.command + after;
            textarea.value = newValue;
            let newCursorPos = wordStart + item.command.length;
            if (item.cursorOffset > 0) newCursorPos = wordStart + item.cursorOffset;
            textarea.setSelectionRange(newCursorPos, newCursorPos);
            isSyncing = true;
            mf.setValue(newValue);
            isSyncing = false;
            if (window.pythonBridge) window.pythonBridge.updateLatex(newValue);
            updateHighlight();

            hideAutocomplete();
            textarea.focus();
        }

        function getTriggerWordAtCursor(text, cursorPos) {
            let searchPos = cursorPos - 1;
            let letters = [];
            let hasBackslash = false;
            while (searchPos >= 0) {
                const ch = text[searchPos];
                if (ch === '\\') { hasBackslash = true; break; }
                else if (/[a-zA-Z]/.test(ch)) { letters.unshift(ch); searchPos--; }
                else break;
            }
            const pureTrigger = letters.join('');
            return { pureTrigger, hasBackslash, fullLength: (hasBackslash ? 1 : 0) + pureTrigger.length };
        }

        function checkAndShowCompletions() {
            const cursorPos = latexOutput.selectionStart;
            const text = latexOutput.value;
            const triggerInfo = getTriggerWordAtCursor(text, cursorPos);
            if (triggerInfo.pureTrigger.length >= 1) {
                const suggestions = latexCompletions.filter(item =>
                    item.trigger.toLowerCase().startsWith(triggerInfo.pureTrigger.toLowerCase())
                );
                if (suggestions.length > 0) { showAutocomplete(suggestions, triggerInfo.pureTrigger); return; }
            }
            hideAutocomplete();
        }

        // ========== 矩阵格式化 ==========
        function formatMatrix(latexStr) {
            const envNames = ['pmatrix', 'bmatrix', 'vmatrix', 'Bmatrix', 'Vmatrix', 'matrix'];
            let result = latexStr;
            for (const envName of envNames) result = formatMatrixEnv(result, envName);
            return result;
        }
        function formatMatrixEnv(latexStr, envName) {
            const beginTag = '\\begin{' + envName + '}';
            const endTag = '\\end{' + envName + '}';
            let result = '', i = 0;
            while (i < latexStr.length) {
                const beginIdx = latexStr.indexOf(beginTag, i);
                if (beginIdx === -1) { result += latexStr.slice(i); break; }
                result += latexStr.slice(i, beginIdx);
                let depth = 1, j = beginIdx + beginTag.length;
                while (j < latexStr.length && depth > 0) {
                    const nextBegin = latexStr.indexOf(beginTag, j);
                    const nextEnd = latexStr.indexOf(endTag, j);
                    if (nextEnd === -1) break;
                    if (nextBegin !== -1 && nextBegin < nextEnd) { depth++; j = nextBegin + beginTag.length; }
                    else { depth--; if (depth === 0) { result += formatMatrixContent(beginTag, endTag, latexStr.slice(beginIdx + beginTag.length, nextEnd)); j = nextEnd + endTag.length; } else { j = nextEnd + endTag.length; } }
                }
                if (depth !== 0) { result += latexStr.slice(beginIdx); break; }
                i = j;
            }
            return result;
        }
        function formatMatrixContent(beginTag, endTag, content) {
            let rows = content.split('\\\\').map(row => row.trim()).filter(row => row.length > 0);
            if (rows.length === 0) return beginTag + content + endTag;
            let cells = rows.map(row => row.split('&').map(cell => cell.trim()));
            let colCount = Math.max(...cells.map(row => row.length));
            let colWidths = Array(colCount).fill(0);
            cells.forEach(row => row.forEach((cell, idx) => { colWidths[idx] = Math.max(colWidths[idx], cell.length); }));
            let alignedRows = cells.map(row => {
                let paddedCells = row.map((cell, idx) => idx < colCount - 1 ? cell.padEnd(colWidths[idx], ' ') : cell);
                return '  ' + paddedCells.join(' & ') + ' \\\\';
            });
            return beginTag + '\n' + alignedRows.join('\n') + '\n' + endTag;
        }
        function autoFormatMatrix() {
            let currentLatex = mf.getValue();
            let formatted = formatMatrix(currentLatex);
            if (formatted !== currentLatex) {
                isSyncing = true; mf.setValue(formatted); isSyncing = false;
                latexOutput.value = formatted;
                updateHighlight();
                if (window.pythonBridge) window.pythonBridge.updateLatex(formatted);
            }
        }

        const debouncedCheckCompletions = debounce(checkAndShowCompletions, 150);
        const debouncedHistorySave = debounce(function() {
            if (window.pythonBridge) window.pythonBridge.saveHistory(mf.getValue());
        }, 2000);

        function onMathFieldInput() {
            if (isSyncing) return;
            const latex = mf.getValue();
            latexOutput.value = latex;
            updateHighlight();

            if (window.pythonBridge) window.pythonBridge.updateLatex(latex);
            debouncedHistorySave();
        }

        function onLatexOutputInput(e) {
            const latex = latexOutput.value;
            const cursorPos = latexOutput.selectionStart;
            if (e.inputType === 'insertText' && e.data) {
                let needsComplete = false, completeChar = '';
                if (e.data === '{') { needsComplete = true; completeChar = '}'; }
                else if (e.data === '(') { needsComplete = true; completeChar = ')'; }
                else if (e.data === '[') { needsComplete = true; completeChar = ']'; }
                if (needsComplete) {
                    const beforeCursor = latex.slice(0, cursorPos);
                    const afterCursor = latex.slice(cursorPos);
                    if (afterCursor[0] !== completeChar) {
                        latexOutput.value = beforeCursor + completeChar + afterCursor;
                        latexOutput.setSelectionRange(cursorPos, cursorPos);
                        isSyncing = true; mf.setValue(latexOutput.value); isSyncing = false;
                        if (window.pythonBridge) window.pythonBridge.updateLatex(latexOutput.value);
                        updateHighlight();
                        debouncedCheckCompletions();
                        return;
                    }
                }
            }
            isSyncing = true; mf.setValue(latex); isSyncing = false;
            if (window.pythonBridge) window.pythonBridge.updateLatex(latex);
            updateHighlight();
            debouncedCheckCompletions();
            debouncedHistorySave();
        }

        function onLatexOutputKeydown(e) {
            if (autocompleteDiv.style.display !== 'block' || currentSuggestions.length === 0) return;
            if (e.key === 'Tab' || e.key === 'Enter') { e.preventDefault(); if (selectedIndex >= 0 && currentSuggestions[selectedIndex]) applyCompletion(currentSuggestions[selectedIndex]); }
            else if (e.key === 'Escape') { e.preventDefault(); hideAutocomplete(); }
            else if (e.key === 'ArrowDown') { e.preventDefault(); selectedIndex = Math.min(selectedIndex + 1, currentSuggestions.length - 1); updateSelectedStyle(); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); selectedIndex = Math.max(selectedIndex - 1, 0); updateSelectedStyle(); }
        }

        function onLatexOutputClickOrMove() { hideAutocomplete(); }

        latexOutput.addEventListener('focus', function() {
            autocompleteDiv.style.display = 'none';
        });

        latexOutput.addEventListener('scroll', function() {
            var pre = document.getElementById('code-highlight');
            if (pre) {
                pre.scrollTop = latexOutput.scrollTop;
                pre.scrollLeft = latexOutput.scrollLeft;
            }
        });

        // 复制按钮由上方独立脚本处理，避免主脚本中途报错导致按钮失效。

        mf.addEventListener('input', onMathFieldInput);
        latexOutput.addEventListener('input', onLatexOutputInput);
        latexOutput.addEventListener('keydown', onLatexOutputKeydown);
        latexOutput.addEventListener('click', onLatexOutputClickOrMove);
        latexOutput.addEventListener('keyup', function(e) {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') hideAutocomplete();
        });

        // ========== 方向键修复 ==========
        mf.addEventListener('focus', function() {
            if (window.pythonBridge) window.pythonBridge.mfFocusChanged(true);
        });
        mf.addEventListener('blur', function() {
            if (window.pythonBridge) window.pythonBridge.mfFocusChanged(false);
        });

        mf.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight' ||
                e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                if (document.activeElement === mf || mf.contains(document.activeElement)) {
                    var commands = {
                        'ArrowLeft': 'moveToPreviousChar',
                        'ArrowRight': 'moveToNextChar',
                        'ArrowUp': 'moveUp',
                        'ArrowDown': 'moveDown'
                    };
                    var cmd = commands[e.key];
                    if (cmd && mf.executeCommand) {
                        e.preventDefault();
                        e.stopPropagation();
                        mf.executeCommand(cmd);
                    }
                }
            }
        }, true);

        document.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight' ||
                e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                if (!mf || !mf.executeCommand) return;
                var path = e.composedPath ? e.composedPath() : [];
                var inMathField = false;
                for (var i = 0; i < path.length; i++) {
                    if (path[i] === mf) { inMathField = true; break; }
                }
                if (!inMathField && document.activeElement !== mf) return;
                var commands = {
                    'ArrowLeft': 'moveToPreviousChar',
                    'ArrowRight': 'moveToNextChar',
                    'ArrowUp': 'moveUp',
                    'ArrowDown': 'moveDown'
                };
                var cmd = commands[e.key];
                if (cmd) {
                    e.preventDefault();
                    e.stopPropagation();
                    mf.executeCommand(cmd);
                }
            }
        }, true);

        function handleArrowKey(direction) {
            if (!mf) return false;
            var commands = {
                'left': 'moveToPreviousChar',
                'right': 'moveToNextChar',
                'up': 'moveUp',
                'down': 'moveDown'
            };
            var cmd = commands[direction];
            if (cmd && mf.executeCommand) {
                mf.executeCommand(cmd);
                return true;
            }
            return false;
        }
        window.handleArrowKey = handleArrowKey;

        function setMathField(latex) {
            if (mf.getValue() !== latex) {
                isSyncing = true; mf.setValue(latex); isSyncing = false;
                latexOutput.value = latex;
                updateHighlight();
            }
        }

        function getMathML() {
            return mf.getValue('math-ml');
        }

        function getLatexValue() {
            return mf.getValue();
        }

        window.onload = function() {
            if (window.qt && window.qt.webChannelTransport) {
                new QWebChannel(window.qt.webChannelTransport, function(channel) {
                    window.pythonBridge = channel.objects.bridge;
                    window.pythonBridge.updateLatex(mf.getValue());
                    window.pythonBridge.requestInitData();
                });
            }
        };

        function formatCurrentMatrix() { autoFormatMatrix(); }
        window.formatCurrentMatrix = formatCurrentMatrix;
        window.setMathField = setMathField;
        window.setZoom = setZoom;
        window.toggleDarkMode = toggleDarkMode;
        window.getMathML = getMathML;
        window.getLatexValue = getLatexValue;

    </script>
</body>
</html>
"""


class Bridge(QObject):
    latexChanged = Signal(str)
    formulaSet = Signal(str)
    historySaveRequested = Signal(str)
    favoritesSaveRequested = Signal(str)
    initRequested = Signal()
    focusStateChanged = Signal(bool)
    languageSaveRequested = Signal(str)
    clipboardCopyRequested = Signal(str)

    def __init__(self):
        super().__init__()
        self.current_latex = ""

    @Slot(str)
    def updateLatex(self, latex):
        self.current_latex = latex
        self.latexChanged.emit(latex)

    @Slot(str)
    def setFormula(self, latex):
        self.formulaSet.emit(latex)

    @Slot(str)
    def saveHistory(self, latex):
        self.historySaveRequested.emit(latex)

    @Slot(str)
    def saveFavorites(self, data_json):
        self.favoritesSaveRequested.emit(data_json)

    @Slot()
    def requestInitData(self):
        self.initRequested.emit()

    @Slot(bool)
    def mfFocusChanged(self, focused):
        self.focusStateChanged.emit(focused)

    @Slot(str)
    def saveLanguage(self, lang):
        self.languageSaveRequested.emit(lang)

    @Slot(str)
    def copyToClipboard(self, text):
        self.clipboardCopyRequested.emit(text)


class MathEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(800, 600)
        self.setAcceptDrops(True)

        self.bundle_dir = get_bundle_dir()
        if getattr(sys, 'frozen', False):
            self.data_dir = os.path.dirname(sys.executable)
        else:
            self.data_dir = self.bundle_dir
        self.current_latex = ""
        self.history = []
        self.favorites = []
        self.is_dark_mode = False
        self.current_font_size = 24
        self.current_lang = self._load_language()

        self.bridge = Bridge()
        self.bridge.latexChanged.connect(self.on_latex_changed_from_js)
        self.bridge.initRequested.connect(self.send_init_data)
        self.bridge.historySaveRequested.connect(self._js_save_history)
        self.bridge.favoritesSaveRequested.connect(self._js_save_favorites)
        self.bridge.focusStateChanged.connect(self._on_mf_focus_changed)
        self.bridge.languageSaveRequested.connect(self._save_language)
        self.bridge.clipboardCopyRequested.connect(self._js_copy_to_clipboard)
        self._mf_focused = False

        self.web_view = QWebEngineView()
        
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        
        self.web_view.setHtml(HTML_CONTENT, QUrl.fromLocalFile(self.bundle_dir + "/"))

        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        self.setCentralWidget(self.web_view)

        self._load_history()
        self._load_favorites()
        self._build_menus()

        self._history_timer = QTimer(self)
        self._history_timer.timeout.connect(self._auto_save_history)
        self._history_timer.start(5000)

        self._update_window_title()
        print(TRANSLATIONS[self.current_lang]["startup_msg"])

    def _load_language(self):
        path = os.path.join(self.data_dir, CONFIG_FILE)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("language", "en")
        except (FileNotFoundError, json.JSONDecodeError):
            return "en"

    def _save_language(self, lang):
        self.current_lang = lang
        path = os.path.join(self.data_dir, CONFIG_FILE)
        try:
            config = {}
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        config["language"] = lang
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        self._update_window_title()
        self._build_menus()

    def _update_window_title(self):
        self.setWindowTitle(TRANSLATIONS[self.current_lang]["window_title"])

    def _switch_language(self, lang):
        if lang == self.current_lang:
            return
        self._save_language(lang)
        self.web_view.page().runJavaScript(f"setLanguage('{lang}');")

    def _build_menus(self):
        menubar = self.menuBar()
        menubar.clear()
        t = TRANSLATIONS[self.current_lang]

        file_menu = menubar.addMenu(t["menu_file"])

        copy_latex_action = QAction(t["action_copy_latex"], self)
        copy_latex_action.setShortcut(QKeySequence("Ctrl+Shift+L"))
        copy_latex_action.triggered.connect(self.copy_latex)
        file_menu.addAction(copy_latex_action)

        copy_img_action = QAction(t["action_copy_image"], self)
        copy_img_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        copy_img_action.triggered.connect(self.copy_as_image)
        file_menu.addAction(copy_img_action)

        export_png_action = QAction(t["action_export_png"], self)
        export_png_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        export_png_action.triggered.connect(lambda: self.export_image("png"))
        file_menu.addAction(export_png_action)

        export_svg_action = QAction(t["action_export_svg"], self)
        export_svg_action.triggered.connect(lambda: self.export_image("svg"))
        file_menu.addAction(export_svg_action)

        file_menu.addSeparator()

        open_action = QAction(t["action_open_tex"], self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_tex_file)
        file_menu.addAction(open_action)

        save_action = QAction(t["action_save_tex"], self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_tex_file)
        file_menu.addAction(save_action)

        tools_menu = menubar.addMenu(t["menu_tools"])

        format_action = QAction(t["action_format_matrix"], self)
        format_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        format_action.triggered.connect(self.format_matrix)
        tools_menu.addAction(format_action)

        tools_menu.addSeparator()

        zoom_in_action = QAction(t["action_zoom_in"], self)
        zoom_in_action.setShortcut(QKeySequence("Ctrl+="))
        zoom_in_action.triggered.connect(lambda: self._change_zoom(2))
        tools_menu.addAction(zoom_in_action)

        zoom_out_action = QAction(t["action_zoom_out"], self)
        zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_action.triggered.connect(lambda: self._change_zoom(-2))
        tools_menu.addAction(zoom_out_action)

        zoom_reset_action = QAction(t["action_zoom_reset"], self)
        zoom_reset_action.setShortcut(QKeySequence("Ctrl+0"))
        zoom_reset_action.triggered.connect(lambda: self._set_zoom(24))
        tools_menu.addAction(zoom_reset_action)

        view_menu = menubar.addMenu(t["menu_view"])

        self.dark_action = QAction(t["action_dark_mode"], self)
        self.dark_action.setCheckable(True)
        self.dark_action.setChecked(self.is_dark_mode)
        self.dark_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(self.dark_action)

        lang_menu = menubar.addMenu(t["menu_language"])
        lang_zh_action = QAction("中文", self)
        lang_zh_action.setCheckable(True)
        lang_zh_action.setChecked(self.current_lang == "zh")
        lang_zh_action.triggered.connect(lambda: self._switch_language("zh"))
        lang_menu.addAction(lang_zh_action)
        lang_en_action = QAction("English", self)
        lang_en_action.setCheckable(True)
        lang_en_action.setChecked(self.current_lang == "en")
        lang_en_action.triggered.connect(lambda: self._switch_language("en"))
        lang_menu.addAction(lang_en_action)

        fav_menu = menubar.addMenu(t["menu_favorites"])

        add_fav_action = QAction(t["action_add_favorite"], self)
        add_fav_action.setShortcut(QKeySequence("Ctrl+D"))
        add_fav_action.triggered.connect(self.add_favorite)
        fav_menu.addAction(add_fav_action)

        fav_menu.addSeparator()
        self._fav_menu = fav_menu
        self._rebuild_fav_menu()

        history_menu = menubar.addMenu(t["menu_history"])
        self._history_menu = history_menu
        self._rebuild_history_menu()

    def _rebuild_fav_menu(self):
        menu = self._fav_menu
        actions_to_remove = [a for a in menu.actions() if a.data() is not None]
        for a in actions_to_remove:
            menu.removeAction(a)
        for i, fav in enumerate(self.favorites):
            label = fav.get("name", fav.get("latex", "")[:30])
            action = QAction(label, self)
            action.setData(i)
            action.triggered.connect(lambda checked, idx=i: self.insert_favorite(idx))
            menu.addAction(action)

    def _rebuild_history_menu(self):
        menu = self._history_menu
        actions_to_remove = [a for a in menu.actions() if a.data() is not None]
        for a in actions_to_remove:
            menu.removeAction(a)
        t = TRANSLATIONS[self.current_lang]
        for i, entry in enumerate(reversed(self.history)):
            latex = entry if isinstance(entry, str) else entry.get("latex", "")
            label = latex[:40] if latex else t["history_empty"]
            action = QAction(label, self)
            action.setData(i)
            action.triggered.connect(lambda checked, idx=len(self.history)-1-i: self.load_history_item(idx))
            menu.addAction(action)

    def _load_history(self):
        path = os.path.join(self.data_dir, HISTORY_FILE)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.history = []

    def _load_favorites(self):
        path = os.path.join(self.data_dir, FAVORITES_FILE)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.favorites = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.favorites = []

    def _persist_history(self):
        path = os.path.join(self.data_dir, HISTORY_FILE)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _persist_favorites(self):
        path = os.path.join(self.data_dir, FAVORITES_FILE)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _js_save_history(self, latex):
        if not latex or not latex.strip():
            return
        if self.history and (self.history[-1] if isinstance(self.history[-1], str) else self.history[-1].get("latex", "")) == latex:
            return
        self.history.append({"latex": latex, "time": time.time()})
        if len(self.history) > MAX_HISTORY:
            self.history = self.history[-MAX_HISTORY:]
        self._persist_history()
        self._rebuild_history_menu()

    def _js_save_favorites(self, data_json):
        try:
            self.favorites = json.loads(data_json)
            self._persist_favorites()
            self._rebuild_fav_menu()
        except json.JSONDecodeError:
            pass

    def _auto_save_history(self):
        if self.current_latex and self.current_latex.strip():
            self._js_save_history(self.current_latex)

    def send_init_data(self):
        self.web_view.page().runJavaScript(f"setLanguage('{self.current_lang}');")
        if self.history:
            last = self.history[-1]
            latex = last if isinstance(last, str) else last.get("latex", "")
            if latex:
                self.set_formula_from_python(latex)
        if self.is_dark_mode:
            self.web_view.page().runJavaScript("toggleDarkMode(true);")

    def on_latex_changed_from_js(self, latex_code):
        self.current_latex = latex_code

    def _on_mf_focus_changed(self, focused):
        self._mf_focused = focused

    def set_formula_from_python(self, latex_code):
        js_literal = json.dumps(latex_code)
        js_code = f"setMathField({js_literal});"
        self.web_view.page().runJavaScript(js_code)

    def format_matrix(self):
        self.web_view.page().runJavaScript("window.formatCurrentMatrix();")

    def copy_latex(self):
        def _copy(latex):
            if latex:
                QApplication.clipboard().setText(latex)
        self.web_view.page().runJavaScript("window.getLatexValue()", _copy)

    def _js_copy_to_clipboard(self, text):
        if text:
            QApplication.clipboard().setText(text)

    def copy_as_image(self):
        pixmap = self.web_view.grab()
        QApplication.clipboard().setPixmap(pixmap)

    def export_image(self, fmt):
        t = TRANSLATIONS[self.current_lang]
        if fmt == "png":
            path, _ = QFileDialog.getSaveFileName(self, t["dialog_export_png"], "formula.png", t["filter_png"])
            if path:
                pixmap = self.web_view.grab()
                pixmap.save(path, "PNG")
        elif fmt == "svg":
            path, _ = QFileDialog.getSaveFileName(self, t["dialog_export_mathml"], "formula.xml", t["filter_xml"])
            if path:
                def _save_mathml(mathml):
                    try:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(mathml or "")
                    except Exception:
                        pass
                self.web_view.page().runJavaScript("window.getMathML()", _save_mathml)

    def open_tex_file(self):
        t = TRANSLATIONS[self.current_lang]
        path, _ = QFileDialog.getOpenFileName(self, t["dialog_open_tex"], "", t["filter_tex"])
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.set_formula_from_python(content)
            except Exception as e:
                QMessageBox.warning(self, t["dialog_open_failed"], str(e))

    def save_tex_file(self):
        t = TRANSLATIONS[self.current_lang]
        path, _ = QFileDialog.getSaveFileName(self, t["dialog_save_tex"], "formula.tex", t["filter_tex"])
        if path:
            def _save_latex(latex):
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(latex or "")
                except Exception:
                    pass
            self.web_view.page().runJavaScript("window.getLatexValue()", _save_latex)

    def toggle_dark_mode(self, checked):
        self.is_dark_mode = checked
        self.web_view.page().runJavaScript(f"toggleDarkMode({str(checked).lower()});")
        if checked:
            self.web_view.setStyleSheet("background: #1e1e1e;")
        else:
            self.web_view.setStyleSheet("")

    def add_favorite(self):
        def _add(latex):
            if not latex or not latex.strip():
                return
            name = latex[:30]
            self.favorites.append({"name": name, "latex": latex})
            self._persist_favorites()
            self._rebuild_fav_menu()
        self.web_view.page().runJavaScript("window.getLatexValue()", _add)

    def insert_favorite(self, idx):
        if 0 <= idx < len(self.favorites):
            latex = self.favorites[idx].get("latex", "")
            if latex:
                self.set_formula_from_python(latex)

    def load_history_item(self, idx):
        if 0 <= idx < len(self.history):
            entry = self.history[idx]
            latex = entry if isinstance(entry, str) else entry.get("latex", "")
            if latex:
                self.set_formula_from_python(latex)

    def _change_zoom(self, delta):
        self.current_font_size = max(12, min(72, self.current_font_size + delta))
        self.web_view.page().runJavaScript(f"setZoom({self.current_font_size});")

    def _set_zoom(self, size):
        self.current_font_size = max(12, min(72, size))
        self.web_view.page().runJavaScript(f"setZoom({self.current_font_size});")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith(('.tex', '.latex', '.txt')):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.endswith(('.tex', '.latex', '.txt')):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.set_formula_from_python(content)
                except Exception:
                    pass
                return


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MathEditorApp()
    window.show()
    sys.exit(app.exec())
