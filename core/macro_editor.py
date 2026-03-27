"""
Script Macro Editor Module - Visual macro editing
Supports conditional judgments, loops, variables, and other functions
"""

import json
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading

import pyautogui

from .logger import get_logger
from .vision import get_vision, MatchResult
from .humanizer import Humanizer, HumanizeConfig

logger = get_logger()


class MacroActionType(Enum):
    """Macro action types"""
    MOVE = "move"                    # Move mouse
    CLICK = "click"                  # Click
    SCROLL = "scroll"                # Scroll
    DELAY = "delay"                  # Delay
    KEY_PRESS = "key_press"          # Key press
    LOOP = "loop"                    # Loop
    CONDITION = "condition"          # Conditional judgment
    VARIABLE = "variable"            # Variable operation
    FIND_IMAGE = "find_image"        # Find image
    GET_COLOR = "get_color"          # Get color
    LOG = "log"                      # Output log


@dataclass
class MacroAction:
    """Macro action"""
    action_type: str
    params: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    enabled: bool = True
    
    def __post_init__(self):
        if not self.id:
            import uuid
            self.id = str(uuid.uuid4())[:8]


@dataclass
class MacroVariable:
    """Macro variable"""
    name: str
    value: Any
    var_type: str = "string"  # string, int, float, bool, point, color


class MacroExecutor:
    """Macro executor"""
    
    def __init__(self):
        self.running = False
        self.paused = False
        self.current_action = 0
        self.variables: Dict[str, MacroVariable] = {}
        self.humanizer = Humanizer(HumanizeConfig())
        self.lock = threading.Lock()
        
        # Callbacks
        self.on_action_start: Optional[Callable] = None
        self.on_action_complete: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        self.on_complete: Optional[Callable] = None
    
    def set_variable(self, name: str, value: Any, var_type: str = "string"):
        """Set variable"""
        self.variables[name] = MacroVariable(name, value, var_type)
        logger.debug(f"Set variable: {name} = {value}")
    
    def get_variable(self, name: str) -> Any:
        """Get variable value"""
        if name in self.variables:
            return self.variables[name].value
        return None
    
    def execute(self, actions: List[MacroAction], loop_count: int = 1) -> bool:
        """
        Execute macro
        
        Args:
            actions: Action list
            loop_count: Loop count
            
        Returns:
            Whether execution was successful
        """
        with self.lock:
            if self.running:
                logger.warning("Macro already executing")
                return False
            
            self.running = True
            self.paused = False
            self.current_action = 0
        
        try:
            for loop in range(loop_count):
                if not self.running:
                    break
                
                logger.info(f"Macro execution - Round {loop + 1}/{loop_count}")
                
                for i, action in enumerate(actions):
                    if not self.running:
                        break
                    
                    # Wait for pause to resume
                    while self.paused:
                        if not self.running:
                            break
                        time.sleep(0.1)
                    
                    self.current_action = i
                    
                    if not action.enabled:
                        continue
                    
                    # Callback
                    if self.on_action_start:
                        self.on_action_start(action, i, len(actions))
                    
                    # Execute action
                    success = self._execute_action(action)
                    
                    if not success:
                        logger.error(f"Action execution failed: {action.action_type}")
                        if self.on_error:
                            self.on_error(action, f"Action execution failed: {action.action_type}")
                    
                    # Callback
                    if self.on_action_complete:
                        self.on_action_complete(action, i, len(actions), success)
            
            if self.on_complete:
                self.on_complete()
            
            logger.info("Macro execution completed")
            return True
            
        except Exception as e:
            logger.error(f"Macro execution exception: {e}")
            if self.on_error:
                self.on_error(None, str(e))
            return False
            
        finally:
            self.running = False
    
    def _execute_action(self, action: MacroAction) -> bool:
        """Execute single action"""
        try:
            params = action.params
            
            if action.action_type == MacroActionType.MOVE.value:
                return self._action_move(params)
            
            elif action.action_type == MacroActionType.CLICK.value:
                return self._action_click(params)
            
            elif action.action_type == MacroActionType.SCROLL.value:
                return self._action_scroll(params)
            
            elif action.action_type == MacroActionType.DELAY.value:
                return self._action_delay(params)
            
            elif action.action_type == MacroActionType.KEY_PRESS.value:
                return self._action_key_press(params)
            
            elif action.action_type == MacroActionType.LOOP.value:
                return self._action_loop(params)
            
            elif action.action_type == MacroActionType.CONDITION.value:
                return self._action_condition(params)
            
            elif action.action_type == MacroActionType.VARIABLE.value:
                return self._action_variable(params)
            
            elif action.action_type == MacroActionType.FIND_IMAGE.value:
                return self._action_find_image(params)
            
            elif action.action_type == MacroActionType.GET_COLOR.value:
                return self._action_get_color(params)
            
            elif action.action_type == MacroActionType.LOG.value:
                return self._action_log(params)
            
            else:
                logger.warning(f"Unknown action type: {action.action_type}")
                return False
                
        except Exception as e:
            logger.error(f"Action execution failed {action.action_type}: {e}")
            return False
    
    def _action_move(self, params: Dict) -> bool:
        """移动鼠标动作"""
        x = self._resolve_value(params.get('x', 0))
        y = self._resolve_value(params.get('y', 0))
        duration = params.get('duration', 0.5)
        smooth = params.get('smooth', True)
        
        if smooth:
            current_x, current_y = pyautogui.position()
            self.humanizer.smooth_move((current_x, current_y), (x, y))
        else:
            pyautogui.moveTo(x, y, duration=duration)
        
        return True
    
    def _action_click(self, params: Dict) -> bool:
        """点击动作"""
        x = self._resolve_value(params.get('x'))
        y = self._resolve_value(params.get('y'))
        button = params.get('button', 'left')
        clicks = params.get('clicks', 1)
        
        if x is not None and y is not None:
            self.humanizer.humanized_click(x, y, button)
        else:
            pyautogui.click(button=button, clicks=clicks)
        
        return True
    
    def _action_scroll(self, params: Dict) -> bool:
        """滚动动作"""
        amount = params.get('amount', 3)
        x = params.get('x')
        y = params.get('y')
        
        if x is not None and y is not None:
            pyautogui.scroll(amount, x=x, y=y)
        else:
            pyautogui.scroll(amount)
        
        return True
    
    def _action_delay(self, params: Dict) -> bool:
        """延迟动作"""
        seconds = params.get('seconds', 1.0)
        random_range = params.get('random_range', 0.0)
        
        if random_range > 0:
            import random
            seconds = random.uniform(seconds - random_range, seconds + random_range)
        
        time.sleep(max(0, seconds))
        return True
    
    def _action_key_press(self, params: Dict) -> bool:
        """按键动作"""
        key = params.get('key', '')
        
        if key:
            pyautogui.press(key)
            return True
        return False
    
    def _action_loop(self, params: Dict) -> bool:
        """循环动作"""
        count = params.get('count', 1)
        actions_data = params.get('actions', [])
        
        actions = [MacroAction(**data) for data in actions_data]
        
        for i in range(count):
            if not self.running:
                break
            for action in actions:
                if not self.running:
                    break
                self._execute_action(action)
        
        return True
    
    def _action_condition(self, params: Dict) -> bool:
        """条件判断动作"""
        condition_type = params.get('condition_type', 'image_found')
        
        condition_met = False
        
        if condition_type == 'image_found':
            image_path = params.get('image_path', '')
            threshold = params.get('threshold', 0.8)
            
            vision = get_vision()
            result = vision.find_template(image_path, threshold=threshold)
            condition_met = result.found
            
            # 保存结果到变量
            if params.get('save_result'):
                self.set_variable(params.get('result_var', 'found'), result.found, 'bool')
                if result.found:
                    self.set_variable(params.get('x_var', 'found_x'), result.x, 'int')
                    self.set_variable(params.get('y_var', 'found_y'), result.y, 'int')
        
        elif condition_type == 'color_match':
            x = params.get('x', 0)
            y = params.get('y', 0)
            expected_color = params.get('color', '')
            
            vision = get_vision()
            color_info = vision.get_pixel_color(x, y)
            condition_met = color_info.hex == expected_color
        
        elif condition_type == 'variable_compare':
            var_name = params.get('var_name', '')
            operator = params.get('operator', '==')
            value = params.get('value')
            
            var_value = self.get_variable(var_name)
            
            if operator == '==':
                condition_met = var_value == value
            elif operator == '!=':
                condition_met = var_value != value
            elif operator == '>':
                condition_met = var_value > value
            elif operator == '<':
                condition_met = var_value < value
            elif operator == '>=':
                condition_met = var_value >= value
            elif operator == '<=':
                condition_met = var_value <= value
        
        # 执行对应分支
        if condition_met:
            true_actions = params.get('true_actions', [])
            for action_data in true_actions:
                if not self.running:
                    break
                self._execute_action(MacroAction(**action_data))
        else:
            false_actions = params.get('false_actions', [])
            for action_data in false_actions:
                if not self.running:
                    break
                self._execute_action(MacroAction(**action_data))
        
        return True
    
    def _action_variable(self, params: Dict) -> bool:
        """变量操作动作"""
        operation = params.get('operation', 'set')
        var_name = params.get('var_name', '')
        
        if operation == 'set':
            value = params.get('value')
            var_type = params.get('var_type', 'string')
            self.set_variable(var_name, value, var_type)
        
        elif operation == 'increment':
            current = self.get_variable(var_name) or 0
            amount = params.get('amount', 1)
            self.set_variable(var_name, current + amount, 'int')
        
        elif operation == 'decrement':
            current = self.get_variable(var_name) or 0
            amount = params.get('amount', 1)
            self.set_variable(var_name, current - amount, 'int')
        
        elif operation == 'get_mouse_pos':
            x, y = pyautogui.position()
            self.set_variable(f"{var_name}_x", x, 'int')
            self.set_variable(f"{var_name}_y", y, 'int')
        
        return True
    
    def _action_find_image(self, params: Dict) -> bool:
        """查找图像动作"""
        image_path = params.get('image_path', '')
        threshold = params.get('threshold', 0.8)
        save_to_var = params.get('save_to_var', 'found')
        
        vision = get_vision()
        result = vision.find_template(image_path, threshold=threshold)
        
        self.set_variable(save_to_var, result.found, 'bool')
        if result.found:
            self.set_variable(f"{save_to_var}_x", result.x, 'int')
            self.set_variable(f"{save_to_var}_y", result.y, 'int')
            self.set_variable(f"{save_to_var}_confidence", result.confidence, 'float')
        
        return result.found if params.get('require_found', False) else True
    
    def _action_get_color(self, params: Dict) -> bool:
        """获取颜色动作"""
        x = params.get('x', 0)
        y = params.get('y', 0)
        save_to_var = params.get('save_to_var', 'color')
        
        vision = get_vision()
        color_info = vision.get_pixel_color(x, y)
        
        self.set_variable(save_to_var, color_info.hex, 'string')
        self.set_variable(f"{save_to_var}_r", color_info.r, 'int')
        self.set_variable(f"{save_to_var}_g", color_info.g, 'int')
        self.set_variable(f"{save_to_var}_b", color_info.b, 'int')
        
        return True
    
    def _action_log(self, params: Dict) -> bool:
        """日志动作"""
        message = params.get('message', '')
        level = params.get('level', 'info')
        
        # 解析变量
        for var_name in self.variables:
            placeholder = f"{{{var_name}}}"
            if placeholder in message:
                message = message.replace(placeholder, str(self.get_variable(var_name)))
        
        if level == 'debug':
            logger.debug(message)
        elif level == 'info':
            logger.info(message)
        elif level == 'warning':
            logger.warning(message)
        elif level == 'error':
            logger.error(message)
        
        return True
    
    def _resolve_value(self, value):
        """解析值（支持变量）"""
        if isinstance(value, str) and value.startswith('$'):
            var_name = value[1:]
            return self.get_variable(var_name)
        return value
    
    def stop(self):
        """停止执行"""
        self.running = False
        logger.info("宏执行已停止")
    
    def pause(self):
        """暂停执行"""
        self.paused = True
        logger.info("宏执行已暂停")
    
    def resume(self):
        """恢复执行"""
        self.paused = False
        logger.info("宏执行已恢复")


class MacroEditor:
    """宏编辑器"""
    
    MACROS_DIR = Path("scripts")
    
    def __init__(self):
        self.MACROS_DIR.mkdir(exist_ok=True)
        self.executor = MacroExecutor()
        self.actions: List[MacroAction] = []
        
        logger.info("Macro editor initialized")
    
    def add_action(self, action: MacroAction):
        """添加动作"""
        self.actions.append(action)
    
    def remove_action(self, action_id: str) -> bool:
        """删除动作"""
        for i, action in enumerate(self.actions):
            if action.id == action_id:
                del self.actions[i]
                return True
        return False
    
    def move_action(self, action_id: str, new_index: int) -> bool:
        """移动动作位置"""
        for i, action in enumerate(self.actions):
            if action.id == action_id:
                action = self.actions.pop(i)
                self.actions.insert(new_index, action)
                return True
        return False
    
    def update_action(self, action_id: str, new_action: MacroAction) -> bool:
        """更新动作"""
        for i, action in enumerate(self.actions):
            if action.id == action_id:
                new_action.id = action_id  # 保持ID不变
                self.actions[i] = new_action
                return True
        return False
    
    def clear(self):
        """清空所有动作"""
        self.actions = []
    
    def save(self, filename: str) -> bool:
        """
        保存宏到文件
        
        Args:
            filename: 文件名（不含扩展名）
            
        Returns:
            是否保存成功
        """
        try:
            data = {
                'version': '1.0',
                'actions': [
                    {
                        'id': action.id,
                        'action_type': action.action_type,
                        'params': action.params,
                        'enabled': action.enabled
                    }
                    for action in self.actions
                ]
            }
            
            filepath = self.MACROS_DIR / f"{filename}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"宏已保存: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"保存宏失败: {e}")
            return False
    
    def load(self, filename: str) -> bool:
        """
        从文件加载宏
        
        Args:
            filename: 文件名（不含扩展名）
            
        Returns:
            是否加载成功
        """
        try:
            filepath = self.MACROS_DIR / f"{filename}.json"
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.actions = []
            for action_data in data.get('actions', []):
                action = MacroAction(
                    id=action_data.get('id', ''),
                    action_type=action_data['action_type'],
                    params=action_data.get('params', {}),
                    enabled=action_data.get('enabled', True)
                )
                self.actions.append(action)
            
            logger.info(f"宏已加载: {filepath}, 共 {len(self.actions)} 个动作")
            return True
            
        except Exception as e:
            logger.error(f"加载宏失败: {e}")
            return False
    
    def export_to_python(self, filename: str) -> bool:
        """导出为Python脚本"""
        try:
            code = f'''"""
自动生成的宏脚本
生成时间: {time.strftime("%Y-%m-%d %H:%M:%S")}
动作数量: {len(self.actions)}
"""

import pyautogui
import time
from core.vision import get_vision
from core.humanizer import Humanizer, HumanizeConfig

humanizer = Humanizer(HumanizeConfig())
vision = get_vision()

def execute_macro():
    """执行宏"""
    print("开始执行宏...")
    
'''
            
            for action in self.actions:
                if not action.enabled:
                    continue
                
                params = action.params
                
                if action.action_type == MacroActionType.MOVE.value:
                    x = params.get('x', 0)
                    y = params.get('y', 0)
                    code += f"    pyautogui.moveTo({x}, {y})\n"
                
                elif action.action_type == MacroActionType.CLICK.value:
                    button = params.get('button', 'left')
                    code += f"    pyautogui.click(button='{button}')\n"
                
                elif action.action_type == MacroActionType.DELAY.value:
                    seconds = params.get('seconds', 1.0)
                    code += f"    time.sleep({seconds})\n"
                
                elif action.action_type == MacroActionType.KEY_PRESS.value:
                    key = params.get('key', '')
                    code += f"    pyautogui.press('{key}')\n"
                
                elif action.action_type == MacroActionType.FIND_IMAGE.value:
                    image_path = params.get('image_path', '')
                    code += f"    result = vision.find_template('{image_path}')\n"
                    code += f"    if result.found:\n"
                    code += f"        pyautogui.moveTo(result.x, result.y)\n"
            
            code += '''
    print("宏执行完成")

if __name__ == "__main__":
    execute_macro()
'''
            
            filepath = self.MACROS_DIR / f"{filename}.py"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)
            
            logger.info(f"Python脚本已导出: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"导出Python脚本失败: {e}")
            return False
    
    def get_actions(self) -> List[MacroAction]:
        """获取所有动作"""
        return self.actions.copy()
    
    def execute(self, loop_count: int = 1) -> bool:
        """执行宏"""
        return self.executor.execute(self.actions, loop_count)
    
    def stop(self):
        """停止执行"""
        self.executor.stop()


# 全局实例
_macro_editor: Optional[MacroEditor] = None


def get_macro_editor() -> MacroEditor:
    """获取宏编辑器实例"""
    global _macro_editor
    if _macro_editor is None:
        _macro_editor = MacroEditor()
    return _macro_editor