"""
Basic Auto-Clicking Module - Implements mouse auto-clicking functionality
Supports multiple click modes, hotkey control
"""

import threading
import time
import random
from typing import Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import pyautogui

from .logger import get_logger
from .humanizer import Humanizer, HumanizeConfig
from .hotkey_manager import get_hotkey_manager, TriggerMode
from core.language_manager import get_language_manager, Language, tr

logger = get_logger()


class ClickButton(Enum):
    """Mouse buttons"""
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


class ClickMode(Enum):
    """Click modes"""
    FIXED = "fixed"       # Fixed interval
    RANDOM = "random"     # Random interval


@dataclass
class ClickConfig:
    """Auto-clicking configuration"""
    # Basic settings
    button: ClickButton = ClickButton.LEFT
    click_mode: ClickMode = ClickMode.FIXED
    
    # Interval settings (seconds)
    interval: float = 0.1                    # Fixed interval
    min_interval: float = 0.05               # Random interval minimum
    max_interval: float = 0.15               # Random interval maximum
    
    # Count settings
    click_count: int = 0                     # 0 means infinite
    
    # Position settings
    use_current_pos: bool = True             # Use current position
    fixed_x: int = 0                         # Fixed position X
    fixed_y: int = 0                         # Fixed position Y
    
    # Hotkey settings
    toggle_hotkey: str = "f8"                # Start/stop hotkey
    hold_mode: bool = False                  # Hold mode
    
    # Humanization settings
    humanize: bool = True                    # Enable humanization simulation
    click_offset: int = 3                    # Click offset radius
    random_delay: bool = True                # Random delay


class AutoClicker:
    """Auto-clicker"""
    
    def __init__(self, config: Optional[ClickConfig] = None):
        self.config = config or ClickConfig()
        self.running = False
        self.paused = False
        self.click_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'total_clicks': 0,
            'start_time': 0,
            'elapsed_time': 0
        }
        
        # Humanization simulator
        if self.config.humanize:
            humanize_config = HumanizeConfig(
                min_delay=0.02,
                max_delay=0.05,
                click_offset_radius=self.config.click_offset
            )
            self.humanizer = Humanizer(humanize_config)
        else:
            self.humanizer = None
        
        # Register hotkeys
        self._register_hotkeys()
        
        logger.info("Auto-clicker initialization completed")
    
    def _register_hotkeys(self):
        """Register hotkeys"""
        hotkey_mgr = get_hotkey_manager()
        
        if self.config.hold_mode:
            # 长按模式
            hotkey_mgr.register(
                self.config.toggle_hotkey,
                self._hold_callback,
                TriggerMode.HOLD,
                tr("autoclicker_start_stop_hotkey")
            )
        else:
            # 切换模式
            hotkey_mgr.register(
                self.config.toggle_hotkey,
                self._toggle_callback,
                TriggerMode.PRESS,
                tr("autoclicker_start_stop")
            )
    
    def _hold_callback(self, is_pressed: bool):
        """长按模式回调"""
        if is_pressed:
            self.start()
        else:
            self.stop()
    
    def _toggle_callback(self):
        """切换模式回调"""
        if self.running:
            self.stop()
        else:
            # 在启动前确保使用最新的配置
            self._sync_config_with_gui()
            self.start()
    
    def _sync_config_with_gui(self):
        """与GUI配置同步"""
        try:
            # 尝试导入GUI模块
            import gui.main_window
            
            # 检查是否有主窗口实例
            if hasattr(gui.main_window, '_main_window_instance'):
                main_window = gui.main_window._main_window_instance
                if main_window and hasattr(main_window, 'get_clicker_config'):
                    # 获取GUI中的配置
                    gui_config = main_window.get_clicker_config()
                    # 更新当前配置
                    self.config = gui_config
                    logger.debug("已同步GUI配置到连点器")
                    return
            logger.debug("GUI模块不可用，使用当前配置")
        except Exception as e:
            logger.debug(f"无法同步GUI配置: {e}")
    
    def start(self) -> bool:
        """开始连点"""
        with self.lock:
            if self.running:
                logger.warning("连点器已在运行")
                return False
            
            self.running = True
            self.paused = False
            self.stats['start_time'] = time.time()
            self.stats['total_clicks'] = 0
            
            # 启动点击线程
            self.click_thread = threading.Thread(target=self._click_loop, daemon=True)
            self.click_thread.start()
            
            logger.info("连点器已启动")
            return True
    
    def stop(self) -> bool:
        """停止连点"""
        with self.lock:
            if not self.running:
                return False
            
            self.running = False
            self.stats['elapsed_time'] = time.time() - self.stats['start_time']
            
            logger.info(f"连点器已停止，共点击 {self.stats['total_clicks']} 次")
            return True
    
    def pause(self):
        """暂停连点"""
        self.paused = True
        logger.info("连点器已暂停")
    
    def resume(self):
        """恢复连点"""
        self.paused = False
        logger.info("连点器已恢复")
    
    def _click_loop(self):
        """点击循环"""
        target_count = self.config.click_count
        
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue
            
            # 检查点击次数
            if target_count > 0 and self.stats['total_clicks'] >= target_count:
                logger.info(f"达到目标点击次数: {target_count}")
                self.stop()
                break
            
            # 执行点击
            self._do_click()
            
            # 计算间隔
            interval = self._get_interval()
            
            # 等待
            time.sleep(interval)
        
        self.running = False
    
    def _do_click(self):
        """执行一次点击"""
        try:
            # 获取点击位置
            if self.config.use_current_pos:
                x, y = pyautogui.position()
            else:
                x, y = self.config.fixed_x, self.config.fixed_y
            
            # 执行点击
            if self.humanizer and self.config.humanize:
                # 人性化点击
                self.humanizer.humanized_click(
                    x, y, 
                    button=self.config.button.value
                )
            else:
                # 普通点击
                if self.config.random_delay and self.config.click_mode == ClickMode.RANDOM:
                    time.sleep(random.uniform(0.01, 0.03))
                
                pyautogui.click(x, y, button=self.config.button.value)
            
            self.stats['total_clicks'] += 1
            
            # 调试日志
            if self.stats['total_clicks'] % 100 == 0:
                logger.debug(f"已点击 {self.stats['total_clicks']} 次")
                
        except Exception as e:
            logger.error(f"点击失败: {e}")
    
    def _get_interval(self) -> float:
        """获取点击间隔"""
        if self.config.click_mode == ClickMode.RANDOM:
            return random.uniform(self.config.min_interval, self.config.max_interval)
        else:
            return self.config.interval
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        stats = self.stats.copy()
        if self.running:
            stats['elapsed_time'] = time.time() - stats['start_time']
        if stats['elapsed_time'] > 0:
            stats['cps'] = stats['total_clicks'] / stats['elapsed_time']
        else:
            stats['cps'] = 0
        return stats
    
    def update_config(self, config: ClickConfig):
        """更新配置"""
        was_running = self.running
        
        if was_running:
            self.stop()
        
        self.config = config
        
        # 重新初始化人性化模拟器
        if self.config.humanize:
            humanize_config = HumanizeConfig(
                min_delay=0.02,
                max_delay=0.05,
                click_offset_radius=self.config.click_offset
            )
            self.humanizer = Humanizer(humanize_config)
        
        # 重新注册热键
        hotkey_mgr = get_hotkey_manager()
        hotkey_mgr.unregister(self.config.toggle_hotkey)
        self._register_hotkeys()
        
        logger.info("连点配置已更新")
    
    def cleanup(self):
        """清理资源"""
        self.stop()
        hotkey_mgr = get_hotkey_manager()
        hotkey_mgr.unregister(self.config.toggle_hotkey)


# 全局连点器实例
_auto_clicker: Optional[AutoClicker] = None


def get_auto_clicker(config: Optional[ClickConfig] = None) -> AutoClicker:
    """获取自动连点器实例"""
    global _auto_clicker
    if _auto_clicker is None:
        _auto_clicker = AutoClicker(config)
    return _auto_clicker