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
