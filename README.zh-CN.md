<div align="center">

[**简体中文**](README.zh-CN.md) | [**English**](README.en.md)

</div>

# HaTeX - 双向 LaTeX 编辑器

基于 PySide6 和 MathLive 构建的桌面 LaTeX 公式编辑器，提供所见即所得的可视化编辑和实时双向代码同步。

## 截图

### 主界面 - 亮色主题
![主界面 - 亮色主题](screenshots/main-light.png)
*双向编辑：上方可视化公式区，下方 LaTeX 代码区，实时同步*

### 主界面 - 暗色主题
![主界面 - 暗色主题](screenshots/main-dark.png)
*亮色/暗色主题切换，舒适编辑*

### 复杂公式
![复杂公式](screenshots/formula-complex.png)
*实时渲染二次方程求根公式*

### 语法高亮
![语法高亮](screenshots/syntax-highlight.png)
*LaTeX 命令、花括号、数字、注释使用不同颜色*

### 自动补全
![自动补全](screenshots/autocomplete.png)
*输入 `\` 后跟命令名，显示智能建议（40+ 命令）*

### 矩阵格式化
![矩阵格式化](screenshots/matrix-format.png)
*Ctrl+Shift+F 自动格式化矩阵环境*

## 功能特性

### 核心功能
- **可视化编辑**：基于 MathLive 的所见即所得公式编辑器
- **双向同步**：可视化公式与 LaTeX 代码实时同步
- **自动补全**：智能 LaTeX 命令补全（40+ 命令）
- **矩阵格式化**：自动格式化矩阵环境（pmatrix、bmatrix、vmatrix 等）
- **语法高亮**：彩色 LaTeX 代码（命令、花括号、数字、注释）

### 高级功能
- **复制 LaTeX**：一键复制 LaTeX 代码到剪贴板（Ctrl+Shift+L）
- **复制为图片**：一键复制公式为 PNG 到剪贴板（Ctrl+Shift+C）
- **导出**：导出为 PNG 或 SVG/MathML
- **历史记录**：自动保存最近 50 个公式，快速调用
- **收藏夹**：收藏常用公式，快速插入
- **拖放支持**：拖入 .tex 文件即可打开
- **缩放控制**：Ctrl+滚轮缩放公式显示（12px–72px）
- **暗色主题**：亮色/暗色主题切换
- **多语言支持**：中文/英文界面切换（默认英文）

## 安装

### 运行环境
- Python 3.8+
- PySide6
- MathLive 0.111.1（已包含）

### 从源码运行
```bash
pip install PySide6
python "HaTeX _v1.5.3.py"
```

### 独立可执行文件
从 [Releases](https://github.com/youyanghu0508/BiDirectional-LaTeX-Editor/releases) 下载 `HaTeX-v1.5.3-windows-x64.zip`，解压后双击 `HaTeX-v1.5.3.exe` 运行。无需安装 Python。

## 使用方法

### 基本操作
1. **输入公式**：在可视化公式区直接输入，或使用虚拟键盘
2. **编辑代码**：在下方代码区直接编辑 LaTeX 代码
3. **自动补全**：在代码区输入 `\` 后跟命令名，按 Tab 或 Enter 选择
4. **格式化矩阵**：选中矩阵代码后按 Ctrl+Shift+F

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+Shift+L | 复制 LaTeX 代码 |
| Ctrl+Shift+C | 复制为 PNG 图片 |
| Ctrl+Shift+E | 导出为 PNG |
| Ctrl+O | 打开 .tex 文件 |
| Ctrl+S | 保存为 .tex 文件 |
| Ctrl+D | 收藏当前公式 |
| Ctrl+Shift+F | 格式化矩阵 |
| Ctrl+= | 放大 |
| Ctrl+- | 缩小 |
| Ctrl+0 | 重置缩放 |
| Ctrl+滚轮 | 缩放公式 |

## 版本历史

### v1.5.3（当前版本）
- **新增**：复制 LaTeX 代码到剪贴板（Ctrl+Shift+L）
- **新增**：代码区标签栏复制按钮
- **新增**：默认语言改为英文
- **修复**：启动时 HTML 标签正确翻译

### v1.5.2
- **新增**：多语言支持（中文/英文）
- **新增**：语言切换菜单（语言 → 中文 / English）
- **新增**：语言偏好保存到配置文件

### v1.5.1
- **修复**：textarea 滚动问题
- **修复**：语法高亮覆盖层滚动同步

### v1.5.0
- **新增**：代码区 LaTeX 语法高亮
- **修复**：公式区方向键导航
- **新增**：PyInstaller 独立可执行文件支持

## 开发者

**胡悠飏 (Youyang Hu)**
中国科学技术大学，少年班，25级
邮箱：youyanghu@mail.ustc.edu.cn

## 许可证

本项目采用 [MIT 许可证](LICENSE)。

---

**当前版本**：v1.5.3 | **最后更新**：2026-10-15
