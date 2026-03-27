"""
Mouse Recording and Playback Module - Records mouse operations and saves as scripts
Supports JSON and Python script formats, supports looped playback
"""

import json
import time
import threading
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

from pynput import mouse, keyboard

from .logger import get_logger
from .humanizer import Humanizer, HumanizeConfig
from .hotkey_manager import get_hotkey_manager, TriggerMode
from core.language_manager import get_language_manager, Language, tr

# Global log signal object (for sending logs to GUI)
_log_signal = None

def set_log_signal(signal):
    """Set global log signal"""
    global _log_signal
    _log_signal = signal

def log_to_gui(level: str, message: str):
    """Send log to GUI"""
    global _log_signal
    if _log_signal:
        from datetime import datetime
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        formatted_message = f"{timestamp} [{level.upper()}] {message}"
        _log_signal.new_log.emit(formatted_message)

logger = get_logger()


class ActionType(Enum):
    """Action types"""
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    MOUSE_SCROLL = "mouse_scroll"
    KEY_PRESS = "key_press"
    DELAY = "delay"


@dataclass
class MouseAction:
    """Mouse action"""
    action_type: str
    x: int = 0
    y: int = 0
    button: str = ""
    pressed: bool = False
    dx: int = 0
    dy: int = 0
    delay: float = 0.0  # Time since previous action
    timestamp: float = 0.0


class MouseRecorder:
    """Mouse recorder"""
    
    def __init__(self, register_hotkeys: bool = True):
        self.recording = False
        self.actions: List[MouseAction] = []
        self.last_action_time: float = 0
        
        self.mouse_listener: Optional[mouse.Listener] = None
        self.keyboard_listener: Optional[keyboard.Listener] = None
        
        self.lock = threading.Lock()
        
        # Recording hotkeys
        self.record_hotkey = "f9"
        self.stop_hotkey = "f10"
        
        # Recording completion callback function
        self.on_record_stopped = None
        
        # Register hotkeys (optional)
        if register_hotkeys:
            self._register_hotkeys()
        
        logger.info("Mouse recorder initialization completed")
        log_to_gui("info", "RECORDER: Mouse recorder initialization completed")
    
    def _register_hotkeys(self):
        """Register hotkeys"""
        hotkey_mgr = get_hotkey_manager()
        hotkey_mgr.register(
            self.record_hotkey,
            self.start_recording,
            TriggerMode.PRESS,
            tr("start_recording")
        )
        hotkey_mgr.register(
            self.stop_hotkey,
            self.stop_recording,
            TriggerMode.PRESS,
            tr("stop_recording")
        )
    
    def start_recording(self) -> bool:
        """开始录制"""
        with self.lock:
            if self.recording:
                logger.warning(tr("recording"))
                log_to_gui("warning", f"RECORDER: {tr('recording')}")
                return False
            
            self.recording = True
            self.actions = []
            self.last_action_time = time.time()
            
            # 启动鼠标监听
            self.mouse_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll
            )
            self.mouse_listener.start()
            
            # 启动键盘监听
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press
            )
            self.keyboard_listener.start()
            
            logger.info(tr("start_recording_mouse"))
            log_to_gui("info", f"RECORDER: {tr('start_recording_mouse')}")
            return True
    
    def stop_recording(self) -> List[MouseAction]:
        """停止录制"""
        with self.lock:
            if not self.recording:
                return []
            
            self.recording = False
            
            # 停止监听
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
            
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
            
            logger.info(f"{tr('recording_finished')},  {len(self.actions)} {tr('actions')}")
            log_to_gui("info", f"RECORDER: {tr('recording_finished')}, {len(self.actions)} {tr('actions')}")
            
            # 如果有录制完成的回调函数，调用它
            if hasattr(self, 'on_record_stopped') and self.on_record_stopped:
                self.on_record_stopped(self.actions.copy())
            
            return self.actions.copy()
    
    def _on_mouse_move(self, x, y):
        """鼠标移动回调"""
        if not self.recording:
            return
        
        # 限制采样率，避免记录过多移动事件
        current_time = time.time()
        if self.actions and self.actions[-1].action_type == ActionType.MOUSE_MOVE.value:
            if current_time - self.actions[-1].timestamp < 0.05:  # 20fps采样
                return
        
        delay = current_time - self.last_action_time
        self.last_action_time = current_time
        
        action = MouseAction(
            action_type=ActionType.MOUSE_MOVE.value,
            x=x,
            y=y,
            delay=delay,
            timestamp=current_time
        )
        
        self.actions.append(action)
    
    def _on_mouse_click(self, x, y, button, pressed):
        """鼠标点击回调"""
        if not self.recording:
            return
        
        current_time = time.time()
        delay = current_time - self.last_action_time
        self.last_action_time = current_time
        
        action = MouseAction(
            action_type=ActionType.MOUSE_CLICK.value,
            x=x,
            y=y,
            button=str(button).split('.')[-1],
            pressed=pressed,
            delay=delay,
            timestamp=current_time
        )
        
        self.actions.append(action)
        logger.debug(f"{tr('record_click')}: ({x}, {y}) {button} {tr('pressed') if pressed else tr('released')}")
        log_to_gui("debug", f"RECORDER: {tr('record_click')}: ({x}, {y}) {button} {tr('pressed') if pressed else tr('released')}")

    def _on_mouse_scroll(self, x, y, dx, dy):
        """鼠标滚轮回调"""
        if not self.recording:
            return
        
        current_time = time.time()
        delay = current_time - self.last_action_time
        self.last_action_time = current_time
        
        action = MouseAction(
            action_type=ActionType.MOUSE_SCROLL.value,
            x=x,
            y=y,
            dx=dx,
            dy=dy,
            delay=delay,
            timestamp=current_time
        )
        
        self.actions.append(action)
    
    def _on_key_press(self, key):
        """键盘按键回调"""
        if not self.recording:
            return
        
        try:
            key_char = key.char
        except AttributeError:
            key_char = str(key)
        
        current_time = time.time()
        delay = current_time - self.last_action_time
        self.last_action_time = current_time
        
        action = MouseAction(
            action_type=ActionType.KEY_PRESS.value,
            button=key_char,
            delay=delay,
            timestamp=current_time
        )
        
        self.actions.append(action)
    
    def save_to_json(self, filepath: str) -> bool:
        """
        保存为JSON格式
        
        Args:
            filepath: 保存路径
            
        Returns:
            是否保存成功
        """
        try:
            data = {
                'version': '1.0',
                'created_at': datetime.now().isoformat(),
                'action_count': len(self.actions),
                'actions': [
                    {
                        'action_type': action.action_type,
                        'x': action.x,
                        'y': action.y,
                        'button': action.button,
                        'pressed': action.pressed,
                        'dx': action.dx,
                        'dy': action.dy,
                        'delay': action.delay,
                        'timestamp': action.timestamp
                    }
                    for action in self.actions
                ]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"{tr('script_saved')}: {filepath}")
            log_to_gui("info", f"RECORDER: {tr('script_saved')}: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"{tr('script_save_failed')}: {e}")    
            log_to_gui("error", f"RECORDER: {tr('script_save_failed')}: {e}")
            return False
    
    def save_to_python(self, filepath: str, script_name: str = "replay_script") -> bool:
        """
        保存为Python脚本
        
        Args:
            filepath: 保存路径
            script_name: 脚本名称
            
        Returns:
            是否保存成功
        """
        try:
            code = f'''"""
自动生成鼠标回放脚本
生成时间: {datetime.now().isoformat()}
动作数量: {len(self.actions)}
"""

import pyautogui
import time
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Controller as KeyboardController

mouse = MouseController()
keyboard = KeyboardController()

def replay():
    """回放录制的操作"""
    print("开始回放...")
    
'''
            
            for action in self.actions:
                if action.delay > 0:
                    code += f"    time.sleep({action.delay:.3f})\n"
                
                if action.action_type == ActionType.MOUSE_MOVE.value:
                    code += f"    pyautogui.moveTo({action.x}, {action.y})\n"
                
                elif action.action_type == ActionType.MOUSE_CLICK.value:
                    btn = action.button.lower()
                    if action.pressed:
                        code += f"    pyautogui.mouseDown(button='{btn}')\n"
                    else:
                        code += f"    pyautogui.mouseUp(button='{btn}')\n"
                
                elif action.action_type == ActionType.MOUSE_SCROLL.value:
                    code += f"    pyautogui.scroll({action.dy}, x={action.x}, y={action.y})\n"
                
                elif action.action_type == ActionType.KEY_PRESS.value:
                    code += f"    pyautogui.press('{action.button}')\n"
            
            code += '''
    print("回放完成")

if __name__ == "__main__":
    replay()
'''
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)
            
            logger.info(f"{tr('script_saved')}: {filepath}")
            log_to_gui("info", f"RECORDER: {tr('script_saved')}: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"{tr('script_save_failed')}: {e}")    
            log_to_gui("error", f"RECORDER: {tr('script_save_failed')}: {e}")

            return False
    
    def load_from_json(self, filepath: str) -> bool:
        """
        从JSON加载脚本
        
        Args:
            filepath: 文件路径
            
        Returns:
            是否加载成功
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.actions = []
            for action_data in data.get('actions', []):
                action = MouseAction(
                    action_type=action_data['action_type'],
                    x=action_data.get('x', 0),
                    y=action_data.get('y', 0),
                    button=action_data.get('button', ''),
                    pressed=action_data.get('pressed', False),
                    dx=action_data.get('dx', 0),
                    dy=action_data.get('dy', 0),
                    delay=action_data.get('delay', 0.0),
                    timestamp=action_data.get('timestamp', 0.0)
                )
                self.actions.append(action)
            
            logger.info(f"{tr('script_loaded')}: {filepath}, {len(self.actions)} {tr('actions')}")
            log_to_gui("info", f"RECORDER: {tr('script_loaded')}: {filepath}, {len(self.actions)} {tr('actions')}")
            return True
            
        except Exception as e:
            logger.error(f"{tr('script_load_failed')}: {e}")
            log_to_gui("error", f"RECORDER: {tr('script_load_failed')}: {e}")

            return False


class ScriptPlayer:
    """脚本播放器"""
    
    def __init__(self):
        self.playing = False
        self.paused = False
        self.current_action = 0
        self.loop_count = 1
        self.current_loop = 0
        
        self.play_thread: Optional[threading.Thread] = None
        self.actions: List[MouseAction] = []
        
        self.lock = threading.Lock()
        
        # 人性化模拟
        self.humanizer = Humanizer(HumanizeConfig())
        
        # 热键
        self.play_hotkey = "f6"
        self.stop_hotkey = "f7"
        
        # 回调
        self.on_action: Optional[Callable] = None
        self.on_complete: Optional[Callable] = None
        
        self._register_hotkeys()
        
        logger.info(tr("script_playerback_init"))
        log_to_gui("info", f"RECORDER: {tr('script_playerback_init')}")
    
    def _register_hotkeys(self):
        """注册热键"""
        hotkey_mgr = get_hotkey_manager()
        hotkey_mgr.register(
            self.play_hotkey,
            self.play,
            TriggerMode.PRESS,
            tr("play_script")
        )
        hotkey_mgr.register(
            self.stop_hotkey,
            self.stop,
            TriggerMode.PRESS,
            tr("stop_playback")
        )
    
    def load_script(self, actions: List[MouseAction]):
        """加载脚本"""
        self.actions = actions.copy()
        logger.info(f"{tr('script_loaded')}: {len(actions)} {tr('actions')}")
        log_to_gui("info", f"RECORDER: {tr('script_loaded')}: {len(actions)} {tr('actions')}")
    
    def load_from_file(self, filepath: str) -> bool:
        """从文件加载脚本"""
        try:
            # 创建不注册热键的临时录制器实例来加载文件
            recorder = MouseRecorder(register_hotkeys=False)
            if recorder.load_from_json(filepath):
                self.load_script(recorder.actions)
                return True
            return False
        except Exception as e:
            logger.error(f"{tr('script_load_failed')}: {e}")
            log_to_gui("error", f"RECORDER: {tr('script_load_failed')}: {e}")
            return False
    
    def play(self, loop_count: int = 1) -> bool:
        """
        开始播放
        
        Args:
            loop_count: 循环次数，0表示无限
            
        Returns:
            是否开始成功
        """
        with self.lock:
            if self.playing:
                logger.warning("已在播放中")
                log_to_gui("warning", "RECORDER: 已在播放中")
                return False
            
            if not self.actions:
                logger.warning("没有加载脚本")
                log_to_gui("warning", "RECORDER: 没有加载脚本")
                return False
            
            self.playing = True
            self.paused = False
            self.current_action = 0
            self.loop_count = loop_count
            self.current_loop = 0
            
            self.play_thread = threading.Thread(target=self._play_loop, daemon=True)
            self.play_thread.start()
            
            logger.info(f"{tr('play_script')}, {tr('loop')} {loop_count if loop_count > 0 else tr('infinite')} {tr('times')}")
            log_to_gui("info", f"RECORDER: {tr('play_script')}, {tr('loop')} {loop_count if loop_count > 0 else tr('infinite')} {tr('times')}")
            return True
    
    def stop(self) -> bool:
        """停止播放"""
        with self.lock:
            if not self.playing:
                return False
            
            self.playing = False
            logger.info(tr("playback_stopped"))
            log_to_gui("info", f"RECORDER: {tr('playback_stopped')}")
            return True
    
    def pause(self):
        """暂停播放"""
        self.paused = True
        logger.info(tr("playback_paused"))
        log_to_gui("info", f"RECORDER: {tr('playback_paused')}")
    
    def resume(self):
        """恢复播放"""
        self.paused = False
        logger.info(tr("playback_resumed"))
        log_to_gui("info", f"RECORDER: {tr('playback_resumed')}")
    
    def _play_loop(self):
        """播放循环"""
        import pyautogui
        
        while self.playing:
            # 检查循环次数
            if self.loop_count > 0 and self.current_loop >= self.loop_count:
                break
            
            self.current_loop += 1
            logger.info(f"{tr('No.')} {self.current_loop} {tr('times')}")
            log_to_gui("info", f"RECORDER: {tr('No.')} {self.current_loop} {tr('times')}")
            
            for i, action in enumerate(self.actions):
                if not self.playing:
                    break
                
                while self.paused:
                    if not self.playing:
                        break
                    time.sleep(0.1)
                
                self.current_action = i
                
                # 执行延迟
                if action.delay > 0:
                    time.sleep(action.delay)
                
                # 执行动作
                self._execute_action(action)
                
                # 回调
                if self.on_action:
                    self.on_action(action, i, len(self.actions))
            
            logger.info(f"{tr('No.')} {self.current_loop} {tr('times')} {tr('completed')}")
            log_to_gui("info", f"RECORDER: {tr('No.')} {self.current_loop} {tr('times')} {tr('completed')}")
            
        self.playing = False
        
        # 完成回调
        if self.on_complete:
            self.on_complete()
        
        logger.info(tr("playback_complete"))
        log_to_gui("info", f"RECORDER: {tr('playback_complete')}")
    
    def _execute_action(self, action: MouseAction):
        """执行单个动作"""
        import pyautogui
        
        try:
            if action.action_type == ActionType.MOUSE_MOVE.value:
                pyautogui.moveTo(action.x, action.y)
            
            elif action.action_type == ActionType.MOUSE_CLICK.value:
                if action.pressed:
                    pyautogui.mouseDown(button=action.button)
                else:
                    pyautogui.mouseUp(button=action.button)
            
            elif action.action_type == ActionType.MOUSE_SCROLL.value:
                pyautogui.scroll(action.dy, x=action.x, y=action.y)
            
            elif action.action_type == ActionType.KEY_PRESS.value:
                pyautogui.press(action.button)
            
        except Exception as e:
            logger.error(f"{tr('execute_action_failed')}: {e}")
            log_to_gui

            
    
    def get_progress(self) -> dict:
        """获取播放进度"""
        return {
            'playing': self.playing,
            'paused': self.paused,
            'current_action': self.current_action,
            'total_actions': len(self.actions),
            'current_loop': self.current_loop,
            'total_loops': self.loop_count,
            'progress_percent': (self.current_action / len(self.actions) * 100) if self.actions else 0
        }


class ScriptManager:
    """脚本管理器"""
    
    SCRIPTS_DIR = Path("scripts")
    
    def __init__(self):
        self.SCRIPTS_DIR.mkdir(exist_ok=True)
        self.recorder = MouseRecorder()
        self.player = ScriptPlayer()
        
        logger.info(tr("script_manager_init"))
        log_to_gui("info", f"RECORDER: {tr('script_manager_init')}")

    
    def get_script_list(self) -> List[Dict]:
        """获取脚本列表"""
        scripts = []
        
        for filepath in self.SCRIPTS_DIR.glob("*.json"):
            try:
                stat = filepath.stat()
                scripts.append({
                    'name': filepath.stem,
                    'filename': filepath.name,
                    'path': str(filepath),
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
            except Exception as e:
                logger.error(f"{tr('script_info_read_failed')} {filepath}: {e}")
                log_to_gui("error", f"RECORDER: {tr('script_info_read_failed')} {filepath}: {e}")
        
        return sorted(scripts, key=lambda x: x['modified'], reverse=True)
    
    def rename_script(self, old_name: str, new_name: str) -> bool:
        """重命名脚本"""
        try:
            old_path = self.SCRIPTS_DIR / f"{old_name}.json"
            new_path = self.SCRIPTS_DIR / f"{new_name}.json"
            
            if not old_path.exists():
                return False
            
            old_path.rename(new_path)
            logger.info(f"{tr('rename_script')} {old_name} -> {new_name}")
            log_to_gui
            return True
            
        except Exception as e:
            logger.error(f"{tr('rename_script_failed')}: {e}")
            log_to_gui
            return False
    
    def delete_script(self, name: str) -> bool:
        """删除脚本"""
        try:
            filepath = self.SCRIPTS_DIR / f"{name}.json"
            
            if not filepath.exists():
                return False
            
            filepath.unlink()
            logger.info(f"{tr('script_deleted')} {name}")
            return True
            
        except Exception as e:
            logger.error(f"{tr('delete_file_failed')}: {e}")
            return False


# 全局实例
_script_manager: Optional[ScriptManager] = None


def get_script_manager() -> ScriptManager:
    """获取脚本管理器实例"""
    global _script_manager
    if _script_manager is None:
        _script_manager = ScriptManager()
    return _script_manager