"""
日志模块 - 提供统一的日志记录功能
支持控制台输出和文件写入，支持调试截图
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import traceback

# 全局日志信号对象（用于发送日志到GUI）
_log_signal = None

def set_log_signal(signal):
    """设置全局日志信号"""
    global _log_signal
    _log_signal = signal

def log_to_gui(level: str, message: str):
    """将日志发送到GUI"""
    global _log_signal
    if _log_signal:
        from datetime import datetime
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        formatted_message = f"{timestamp} [{level.upper()}] {message}"
        _log_signal.new_log.emit(formatted_message)


class AppLogger:
    """应用程序日志管理器"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, log_dir: str = "logs", log_level: int = logging.DEBUG):
        if self._initialized:
            return
            
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.screenshot_dir = Path("screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger("PigBabyMouse")
        self.logger.setLevel(log_level)
        
        # 清除已有处理器
        self.logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        log_file = self.log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        self._initialized = True
        self.info("Logger initialized")
    
    def debug(self, message: str):
        """记录调试信息"""
        self.logger.debug(message)
        log_to_gui("debug", message)
    
    def info(self, message: str):
        """记录普通信息"""
        self.logger.info(message)
        log_to_gui("info", message)
    
    def warning(self, message: str):
        """记录警告信息"""
        self.logger.warning(message)
        log_to_gui("warning", message)
    
    def error(self, message: str, exc_info: bool = False):
        """记录错误信息"""
        self.logger.error(message, exc_info=exc_info)
        log_to_gui("error", message)
        if exc_info:
            self.take_screenshot("error")
    
    def critical(self, message: str, exc_info: bool = True):
        """记录严重错误"""
        self.logger.critical(message, exc_info=exc_info)
        log_to_gui("critical", message)
        self.take_screenshot("critical")
    
    def take_screenshot(self, prefix: str = "debug") -> Optional[str]:
        """
        Capture screenshot
        
        Args:
            prefix: File name prefix
            
        Returns:
            Screenshot file path, returns None if failed
        """
        try:
            import pyautogui
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{prefix}_{timestamp}.png"
            filepath = self.screenshot_dir / filename
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            self.info(f"Screenshot saved: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return None
    
    def log_exception(self, e: Exception, context: str = ""):
        """
        Record exception information
        
        Args:
            e: Exception object
            context: Context information
        """
        error_msg = f"{context} - Exception: {type(e).__name__}: {str(e)}" if context else f"Exception: {type(e).__name__}: {str(e)}"
        self.error(error_msg, exc_info=True)


# Global logger instance
logger = AppLogger()


def get_logger() -> AppLogger:
    """Get logger instance"""
    return logger