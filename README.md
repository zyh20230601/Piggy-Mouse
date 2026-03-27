# PigBaby Mouse Automation Tool

A comprehensive mouse automation tool that supports basic auto-clicking, mouse recording and playback, image recognition, macro editing, and other features.

## Features

### 1. Basic Auto-Clicking Module
- Supports left, right, and middle button clicks
- Fixed interval or random interval mode (0.01~10 seconds)
- Can set total click count or infinite clicking
- Supports fixed coordinates or current mouse position clicking
- Global hotkey (default F8) start/stop
- Optional long-press trigger mode

### 2. Mouse Recording and Playback
- Records mouse clicks, movements, and scroll wheel events
- Saves as JSON or Python script format
- Script library management: list, rename, delete, load
- Supports playback with specified loop count
- Each script can have its own startup hotkey

### 3. Image and Text Recognition
- Image template matching with similarity threshold support
- Multi-scale matching to adapt to different icon sizes
- Text recognition (OCR, optional)
- Color recognition: get pixel color at specified coordinates
- Area monitoring: periodically detect specific icons or colors

### 4. Script Macro Editor
- Visual macro editing
- Supported actions: move, click, wait, loop, conditional judgment
- Conditional judgment: based on icon presence, color matching, etc.
- Variable and parameter support
- Macro script import/export

### 5. Hotkey and Trigger Mechanism
- Global start/stop hotkeys (default F6/F7)
- Trigger modes: single trigger, long-press hold, toggle mode
- Mouse trigger support
- Supports customizing all hotkeys

### 6. Humanized Simulation
- Random delay: random delay before each operation
- Click offset: random offset around target coordinates
- Smooth movement: Bezier curves or random jitter
- Behavior statistics: record operation frequency

### 7. Debugging and Logging
- Console output logging, simultaneously written to files
- Automatic screenshots at key steps or errors
- Step highlighting: rectangle marks the position of recognized icons

## System Requirements

- **Operating System**: Windows 7/10/11
- **Python Version**: Python 3.8+
- **Permissions**: Recommended to run as administrator to handle some games

## Installation Method

### 1. Clone or Download the Project

```bash
git clone <repository_url>
cd pigbaby_mouse
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Tesseract (Optional, for OCR)

If you need to use text recognition functionality, install Tesseract:

1. Download installer: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to default path: `C:\Program Files\Tesseract-OCR`
3. Install Chinese language pack

## Usage

### Start Program

```bash
python main.py
```

### 热键说明

| 热键 | 功能 |
|------|------|
| F6 | 播放脚本 |
| F7 | 停止播放 |
| F8 | 启动/停止连点器 |
| F9 | 开始录制 |
| F10 | 停止录制 |

### 基础连点

1. 切换到"基础连点"标签页
2. 选择鼠标按钮（左/右/中）
3. 设置点击间隔（固定或随机）
4. 设置点击次数或选择无限点击
5. 选择点击位置（当前位置或固定坐标）
6. 点击"开始连点"或按F8

### 录制与回放

1. 切换到"录制回放"标签页
2. 按F9开始录制
3. 执行需要录制的鼠标操作
4. 按F10停止录制
5. 保存脚本
6. 选择脚本，按F6播放

### 图像识别

1. 切换到"图像识别"标签页
2. 选择模板图像
3. 设置相似度阈值
4. 点击"查找模板"
5. 查看匹配结果

### 宏编辑

1. 切换到"宏编辑"标签页
2. 添加需要的动作
3. 调整动作参数
4. 保存宏脚本
5. 点击"运行宏"

## 项目结构

```
pigbaby_mouse/
├── core/                   # 核心功能模块
│   ├── __init__.py
│   ├── auto_clicker.py    # 自动连点器
│   ├── recorder.py        # 录制与回放
│   ├── vision.py          # 图像识别
│   ├── hotkey_manager.py  # 热键管理
│   ├── humanizer.py       # 人性化模拟
│   ├── macro_editor.py    # 宏编辑器
│   └── logger.py          # 日志模块
├── gui/                    # 图形界面
│   ├── __init__.py
│   └── main_window.py     # 主窗口
├── scripts/                # 脚本存储目录
│   ├── example_click.json
│   └── example_macro.json
├── images/                 # 图像存储目录
├── logs/                   # 日志存储目录
├── config/                 # 配置文件目录
├── screenshots/            # 截图存储目录
├── main.py                 # 主程序入口
├── requirements.txt        # 依赖列表
└── README.md              # 说明文档
```

## 依赖列表

- PyQt5 >= 5.15.0 - 图形界面
- pyautogui >= 0.9.54 - 鼠标控制
- pynput >= 1.7.6 - 鼠标监听
- keyboard >= 0.13.5 - 热键监听
- opencv-python >= 4.8.0 - 图像识别
- numpy >= 1.24.0 - 数值计算
- Pillow >= 10.0.0 - 图像处理
- pytesseract >= 0.3.10 - OCR（可选）
- pywin32 >= 306 - Windows API
- psutil >= 5.9.0 - 系统信息
- scipy >= 1.11.0 - 科学计算

## 性能指标

- 图像识别每帧耗时 < 200ms
- 连点延迟误差 < 5ms
- 支持后台运行

## 注意事项

1. **管理员权限**: 建议以管理员权限运行，特别是在游戏中使用时
2. **防检测**: 启用人性化模拟功能可以降低被检测的风险
3. **热键冲突**: 确保设置的热键不会与其他应用程序冲突
4. **安全性**: 不要在不信任的来源下载脚本文件

## Frequently Asked Questions

### Q: Program won't start?
A: Please check if Python version is >=3.8, and ensure all dependencies are properly installed.

### Q: Hotkeys not working?
A: Make sure the program has sufficient permissions, try running as administrator.

### Q: Image recognition not accurate?
A: Try adjusting the similarity threshold, or use multi-scale matching feature.

### Q: Can't use in games?
A: Some games may have anti-cheat mechanisms, recommended to run as administrator and enable humanized simulation.

## Changelog

### v1.0.0 (2024-01-01)
- Initial version release
- Implemented basic auto-clicking functionality
- Implemented mouse recording and playback
- Implemented image recognition functionality
- Implemented macro editor
- Implemented global hotkey support

## License

MIT License

## Contact

If you have questions or suggestions, welcome to submit Issues or Pull Requests.

---

**Disclaimer**: This tool is for learning and legal purposes only. Do not use it for actions that violate game terms or laws and regulations. Users are responsible for any consequences resulting from the use of this tool.