"""
Hotkey Management Module - Global hotkey listening and management
Supports custom hotkeys, multiple trigger modes
"""

import threading
import time
from typing import Callable, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import keyboard

from .logger import get_logger

logger = get_logger()


class TriggerMode(Enum):
    """Trigger modes"""
    PRESS = "press"           # Trigger on press
    RELEASE = "release"       # Trigger on release
    HOLD = "hold"             # Hold mode
    TOGGLE = "toggle"         # Toggle mode (press once to turn on, press again to turn off)


@dataclass
class HotkeyConfig:
    """Hotkey configuration"""
    key: str                          # Hotkey (e.g., 'f8', 'ctrl+shift+a')
    callback: Callable                # Callback function
    trigger_mode: TriggerMode = TriggerMode.PRESS
    description: str = ""             # Description
    enabled: bool = True              # Whether enabled
    is_pressed: bool = False          # Whether currently pressed (internal state)
    is_active: bool = False           # Active state (for toggle mode)


class HotkeyManager:
    """Hotkey manager"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.hotkeys: Dict[str, HotkeyConfig] = {}
        self.running = False
        self.listener_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Record key press state
        self.pressed_keys: Set[str] = set()
        
        self._initialized = True
        logger.info("Hotkey manager initialization completed")
    
    def register(
        self, 
        key: str, 
        callback: Callable,
        trigger_mode: TriggerMode = TriggerMode.PRESS,
        description: str = ""
    ) -> bool:
        """
        Register hotkey
        
        Args:
            key: Hotkey combination (e.g., 'f8', 'ctrl+shift+a')
            callback: Callback function
            trigger_mode: Trigger mode
            description: Hotkey description
            
        Returns:
            Whether registration was successful
        """
        try:
            with self.lock:
                # Normalize hotkey string
                key = self._normalize_key(key)
                
                if key in self.hotkeys:
                    logger.warning(f"Hotkey {key} already registered, will be overwritten")
                    self.unregister(key)
                
                config = HotkeyConfig(
                    key=key,
                    callback=callback,
                    trigger_mode=trigger_mode,
                    description=description
                )
                
                self.hotkeys[key] = config
                
                # Register keyboard listener
                self._setup_keyboard_hook(key, config)
                
                logger.info(f"Hotkey registered successfully: {key} ({description})")
                return True
                
        except Exception as e:
            logger.error(f"Hotkey registration failed {key}: {e}")
            return False
    
    def unregister(self, key: str) -> bool:
        """
        Unregister hotkey
        
        Args:
            key: Hotkey
            
        Returns:
            Whether unregistration was successful
        """
        try:
            with self.lock:
                key = self._normalize_key(key)
                
                if key not in self.hotkeys:
                    return False
                
                del self.hotkeys[key]
                keyboard.unhook_key(key)
                
                logger.info(f"Hotkey unregistered successfully: {key}")
                return True
                
        except Exception as e:
            logger.error(f"Hotkey unregistration failed {key}: {e}")
            return False
    
    def _normalize_key(self, key: str) -> str:
        """Normalize hotkey string"""
        key = key.lower().replace(' ', '')
        # Unify separator
        key = key.replace('+', '+')
        return key
    
    def _setup_keyboard_hook(self, key: str, config: HotkeyConfig):
        """Set up keyboard hook - Use more reliable global hotkey registration"""
        
        # Add debug information, check if the passed key and config match
        logger.debug(f"_setup_keyboard_hook called: key={key}, config.key={config.key}")
        
        # Check if key and config.key are consistent
        if key != config.key:
            logger.error(f"Hotkey configuration mismatch! Passed key={key}, but config.key={config.key}")
            # Use config.key as the correct key value
            key = config.key
            logger.info(f"Automatically fixed hotkey configuration, using correct key: {key}")
        
        def on_key_event(event):
            """Handle keyboard events - Get corresponding config based on actual pressed key"""
            if not self.running:
                return
                
            event_name = event.name.lower() if event.name else ""
            
            # Add debug information, check key events
            logger.debug(f"Key event: event_name={event_name}")
            
            if event.event_type == 'down':
                self.pressed_keys.add(event_name)
                
                # Find corresponding configuration based on pressed key
                matched_config = None
                for hotkey_key, hotkey_config in self.hotkeys.items():
                    if not hotkey_config.enabled:
                        continue
                    
                    # Check if it's the currently pressed hotkey
                    if self._is_hotkey_pressed(hotkey_key):
                        matched_config = hotkey_config
                        logger.debug(f"Found matching hotkey configuration: {hotkey_key}")
                        break

                if not matched_config:
                    return
            
                # Check if it's the target hotkey
                if self._is_hotkey_pressed(matched_config.key):
                    self._handle_trigger(matched_config, True)

                if event_name.lower() != "f8":
                    self.pressed_keys.discard(event_name)  # Remove immediately to avoid repeated triggers
                    # Check if it's the target hotkey release
                    if self._was_hotkey_pressed(matched_config.key):
                        self._handle_trigger(matched_config, False)

            elif event.event_type == 'up':
                self.pressed_keys.discard(event_name)
                
                # Check if it's the target hotkey release
                if self._was_hotkey_pressed(matched_config.key):
                    self._handle_trigger(matched_config, False)
        
        # Use more reliable global hotkey registration method
        try:
            # First try using add_hotkey method (more reliable global hotkey)
            if '+' in key:
                # Use add_hotkey for combination keys
                keyboard.add_hotkey(key, lambda: self._handle_trigger(config, True))
            else:
                # Use on_press/on_release for single keys
                keyboard.on_press(on_key_event)
                keyboard.on_release(on_key_event)
            
            logger.debug(f"Hotkey registered successfully (global): {key}")
            
        except Exception as e:
            logger.warning(f"Global hotkey registration failed {key}, using fallback: {e}")
            # Fallback: use original method
            keyboard.on_press(on_key_event)
            keyboard.on_release(on_key_event)
    
    def _is_hotkey_pressed(self, hotkey: str) -> bool:
        """Check if hotkey is pressed"""
        keys = hotkey.split('+')
        return all(k in self.pressed_keys for k in keys)
    
    def _was_hotkey_pressed(self, hotkey: str) -> bool:
        """Check if hotkey was just released"""
        # Simplified processing: check whenever any key is released
        keys = hotkey.split('+')
        return any(k not in self.pressed_keys for k in keys) and len(self.pressed_keys) < len(keys)
    
    def _handle_trigger(self, config: HotkeyConfig, is_press: bool):
        """Handle trigger"""
        try:
            if config.trigger_mode == TriggerMode.PRESS and is_press:
                if not config.is_pressed or config.key.lower() == "f8":  # F8 allows repeated triggers
                    config.is_pressed = True
                    logger.debug(f"Hotkey triggered (PRESS): {config.key}")
                    threading.Thread(target=config.callback, daemon=True).start()
                else:
                    logger.debug(f"Hotkey already pressed, ignoring repeated trigger: {config.key}")
                    
            elif config.trigger_mode == TriggerMode.PRESS and not is_press:
                # Reset state when key is released
                config.is_pressed = False
                logger.debug(f"Hotkey released (PRESS): {config.key}")
                    
            elif config.trigger_mode == TriggerMode.RELEASE and not is_press:
                logger.debug(f"Hotkey triggered (RELEASE): {config.key}")
                threading.Thread(target=config.callback, daemon=True).start()
                config.is_pressed = False
                
            elif config.trigger_mode == TriggerMode.HOLD:
                config.is_pressed = is_press
                logger.debug(f"Hotkey status (HOLD): {config.key} = {is_press}")
                threading.Thread(target=config.callback, args=(is_press,), daemon=True).start()
                
            elif config.trigger_mode == TriggerMode.TOGGLE and is_press:
                config.is_active = not config.is_active
                logger.debug(f"Hotkey triggered (TOGGLE): {config.key} = {config.is_active}")
                threading.Thread(target=config.callback, args=(config.is_active,), daemon=True).start()
                
        except Exception as e:
            logger.error(f"Hotkey callback execution failed {config.key}: {e}")
    
    def enable(self, key: str) -> bool:
        """Enable hotkey"""
        key = self._normalize_key(key)
        if key in self.hotkeys:
            self.hotkeys[key].enabled = True
            logger.info(f"Hotkey enabled: {key}")
            return True
        return False
    
    def disable(self, key: str) -> bool:
        """Disable hotkey"""
        key = self._normalize_key(key)
        if key in self.hotkeys:
            self.hotkeys[key].enabled = False
            logger.info(f"Hotkey disabled: {key}")
            return True
        return False
    
    def start(self):
        """Start hotkey listening"""
        if self.running:
            return
        
        self.running = True
        logger.info("Hotkey manager started")
    
    def stop(self):
        """Stop hotkey listening"""
        if not self.running:
            return
        
        self.running = False
        
        # Unregister all hotkeys
        for key in list(self.hotkeys.keys()):
            self.unregister(key)
        
        keyboard.unhook_all()
        logger.info("Hotkey manager stopped")
    
    def get_hotkey_list(self) -> list:
        """Get all hotkey list"""
        return [
            {
                'key': config.key,
                'description': config.description,
                'trigger_mode': config.trigger_mode.value,
                'enabled': config.enabled
            }
            for config in self.hotkeys.values()
        ]
    
    def is_key_pressed(self, key: str) -> bool:
        """Check if a specific key is pressed"""
        return key.lower() in self.pressed_keys


# Global hotkey manager instance
hotkey_manager = HotkeyManager()


def get_hotkey_manager() -> HotkeyManager:
    """Get hotkey manager instance"""
    return hotkey_manager