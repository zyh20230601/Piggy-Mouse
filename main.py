#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PigBaby Mouse Automation Tool - Main Entry

Usage:
    python main.py

Features:
    - Basic mouse auto-clicking
    - Mouse recording and playback
    - Image recognition and template matching
    - Macro editing and execution
    - Global hotkey control

Hotkey Guide:
    F6 - Play script
    F7 - Stop playback
    F8 - Start/stop auto-clicker
    F9 - Start recording
    F10 - Stop recording
"""

import sys
import os
from pathlib import Path

# Ensure correct working directory
project_root = Path(__file__).parent.absolute()
os.chdir(project_root)

# Add project root to Python path
sys.path.insert(0, str(project_root))

# Import GUI
from gui.main_window import main

if __name__ == "__main__":
    # Check administrator privileges (Windows)
    if sys.platform == 'win32':
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print("Note: Recommended to run as administrator for best compatibility")
                print("Tip: Run as administrator for best compatibility")
        except:
            pass
    
    # Start application
    main()