"""
Language Manager - Provides internationalization support for English and Chinese
Supports dynamic language switching and text translation
"""

import json
from pathlib import Path
from typing import Dict, Any
from enum import Enum
from dataclasses import dataclass

from .logger import get_logger

logger = get_logger()


class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    CHINESE = "zh"


@dataclass
class LanguageConfig:
    """Language configuration"""
    current_language: Language = Language.ENGLISH
    fallback_language: Language = Language.ENGLISH


class LanguageManager:
    """Language manager for internationalization"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config = LanguageConfig()
        self.translations: Dict[str, Dict[str, str]] = {}
        self.callbacks = []
        
        # Load language files
        self._load_languages()
        
        self._initialized = True
        logger.info("Language manager initialized")
    
    def _load_languages(self):
        """Load language files from the languages directory"""
        languages_dir = Path(__file__).parent.parent / "languages"
        languages_dir.mkdir(exist_ok=True)
        
        # Load English translations
        en_file = languages_dir / "en.json"
        if en_file.exists():
            with open(en_file, 'r', encoding='utf-8') as f:
                self.translations[Language.ENGLISH.value] = json.load(f)
        else:
            # Create default English translations
            self.translations[Language.ENGLISH.value] = self._get_default_english()
            with open(en_file, 'w', encoding='utf-8') as f:
                json.dump(self.translations[Language.ENGLISH.value], f, indent=2, ensure_ascii=False)
        
        # Load Chinese translations
        zh_file = languages_dir / "zh.json"
        if zh_file.exists():
            with open(zh_file, 'r', encoding='utf-8') as f:
                self.translations[Language.CHINESE.value] = json.load(f)
        else:
            # Create default Chinese translations
            self.translations[Language.CHINESE.value] = self._get_default_chinese()
            with open(zh_file, 'w', encoding='utf-8') as f:
                json.dump(self.translations[Language.CHINESE.value], f, indent=2, ensure_ascii=False)
    
    def _get_default_english(self) -> Dict[str, str]:
        """Get default English translations"""
        return {
            # Main window
            "main_window_title": "PigBaby Mouse Automation Tool v1.0",
            "tab_autoclick": "Basic Auto-Clicking",
            "tab_recorder": "Recording Playback",
            "tab_vision": "Image Recognition",
            "tab_macro": "Macro Editor",
            "tab_settings": "Settings",
            "log_group": "Runtime Log",
            "clear_log": "Clear Log",
            "save_log": "Save Log",
            
            # Auto-clicker tab
            "mouse_button": "Mouse Button",
            "click_interval": "Click Interval",
            "mode": "Mode",
            "fixed_interval": "Fixed Interval",
            "random_interval": "Random Interval",
            "interval_seconds": "Interval (seconds)",
            "min": "Min",
            "max": "Max",
            "click_count": "Click Count",
            "infinite_clicks": "Infinite clicks",
            "count": "Count",
            "click_position": "Click Position",
            "use_current_mouse_position": "Use current mouse position",
            "pick_position": "Pick Position",
            "hotkey_settings": "Hotkey Settings",
            "start_stop": "Start/Stop",
            "hold_mode": "Hold mode",
            "humanization_simulation": "Humanization Simulation",
            "enable_humanization_simulation": "Enable humanization simulation",
            "click_offset_pixels": "Click offset (pixels)",
            "start_autoclick": "Start Auto-Click (F8)",
            "stop_autoclick": "Stop Auto-Click",
            "status": "Status",
            "status_stopped": "Stopped",
            "status_running": "Running",
            "clicks": "Clicks",
            "runtime": "Runtime",
            "cps": "CPS",
            
            # Recorder tab
            "recording_control": "Recording Control",
            "start_recording": "Start Recording (F9)",
            "stop_recording": "Stop Recording (F10)",
            "playback_control": "Playback Control",
            "play_script": "Play Script (F6)",
            "stop_script": "Stop (F7)",
            "loop": "Loop",
            "script_list": "Script List",
            "load": "Load",
            "delete": "Delete",
            "refresh": "Refresh",
            
            # Settings
            "general_settings": "General Settings",
            "language": "Language",
            "english": "English",
            "chinese": "Chinese",
            "apply": "Apply",
            "restart_required": "Restart required for language changes",
            
            # Status messages
            "ready": "Ready",
            "recording": "Recording",
            "playing": "Playing",
            "stopped": "Stopped",
            "paused": "Paused"
        }
    
    def _get_default_chinese(self) -> Dict[str, str]:
        """Get default Chinese translations"""
        return {
            # Main window
            "main_window_title": "猪宝宝鼠标自动化工具 v1.0",
            "tab_autoclick": "基础连点",
            "tab_recorder": "录制回放",
            "tab_vision": "图像识别",
            "tab_macro": "宏编辑器",
            "tab_settings": "设置",
            "log_group": "运行日志",
            "clear_log": "清空日志",
            "save_log": "保存日志",
            
            # Auto-clicker tab
            "mouse_button": "鼠标按钮",
            "click_interval": "点击间隔",
            "mode": "模式",
            "fixed_interval": "固定间隔",
            "random_interval": "随机间隔",
            "interval_seconds": "间隔(秒)",
            "min": "最小",
            "max": "最大",
            "click_count": "点击次数",
            "infinite_clicks": "无限点击",
            "count": "次数",
            "click_position": "点击位置",
            "use_current_mouse_position": "使用鼠标当前位置",
            "pick_position": "拾取位置",
            "hotkey_settings": "热键设置",
            "start_stop": "启动/停止",
            "hold_mode": "长按模式",
            "humanization_simulation": "人性化模拟",
            "enable_humanization_simulation": "启用人性化模拟",
            "click_offset_pixels": "点击偏移(像素)",
            "start_autoclick": "开始连点 (F8)",
            "stop_autoclick": "停止连点",
            "status": "状态",
            "status_stopped": "已停止",
            "status_running": "运行中",
            "clicks": "点击次数",
            "runtime": "运行时间",
            "cps": "CPS",
            
            # Recorder tab
            "recording_control": "录制控制",
            "start_recording": "开始录制 (F9)",
            "stop_recording": "停止录制 (F10)",
            "playback_control": "回放控制",
            "play_script": "播放脚本 (F6)",
            "stop_script": "停止 (F7)",
            "loop": "循环",
            "script_list": "脚本列表",
            "load": "加载",
            "delete": "删除",
            "refresh": "刷新",
            
            # Settings
            "general_settings": "通用设置",
            "language": "语言",
            "english": "英文",
            "chinese": "中文",
            "apply": "应用",
            "restart_required": "语言更改需要重启",
            
            # Status messages
            "ready": "就绪",
            "recording": "录制中",
            "playing": "播放中",
            "stopped": "已停止",
            "paused": "已暂停"
        }
    
    def set_language(self, language: Language):
        """Set current language"""
        self.config.current_language = language
        logger.info(f"Language set to: {language.value}")
        
        # Notify all registered callbacks
        for callback in self.callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in language change callback: {e}")
    
    def get_text(self, key: str) -> str:
        """Get translated text for the given key"""
        current_lang = self.config.current_language.value
        fallback_lang = self.config.fallback_language.value
        
        # Try current language first
        if current_lang in self.translations and key in self.translations[current_lang]:
            return self.translations[current_lang][key]
        
        # Fallback to fallback language
        if fallback_lang in self.translations and key in self.translations[fallback_lang]:
            return self.translations[fallback_lang][key]
        
        # Return key as fallback
        logger.warning(f"Translation key not found: {key}")
        return key
    
    def register_callback(self, callback):
        """Register a callback for language changes"""
        self.callbacks.append(callback)
    
    def unregister_callback(self, callback):
        """Unregister a callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)


# Global language manager instance
_language_manager: LanguageManager = None


def get_language_manager() -> LanguageManager:
    """Get language manager instance"""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager


def tr(key: str) -> str:
    """Shortcut function for translation"""
    return get_language_manager().get_text(key)