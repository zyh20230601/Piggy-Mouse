"""
Main Window - Main interface for PigBaby Mouse Automation Tool
"""

import sys
import os
from pathlib import Path
from core.language_manager import get_language_manager, Language, tr

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTabWidget, QGroupBox,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
    QLineEdit, QTextEdit, QPlainTextEdit, QListWidget, QListWidgetItem,
    QMessageBox, QFileDialog, QProgressBar, QSplitter,
    QFrame, QStatusBar, QMenuBar, QMenu, QAction,
    QApplication, QSystemTrayIcon, QStyle
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QIcon, QFont, QTextCursor

# Add project root directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logger import get_logger
from core.auto_clicker import get_auto_clicker, ClickConfig, ClickButton, ClickMode
from core.recorder import get_script_manager
from core.hotkey_manager import get_hotkey_manager
from core.vision import get_vision
from core.macro_editor import get_macro_editor, MacroAction, MacroActionType

logger = get_logger()
VERSION="0.3"

class LogSignal(QObject):
    """Log signal"""
    new_log = pyqtSignal(str)


class LogHandler:
    """Log handler"""
    
    def __init__(self, signal: LogSignal):
        self.signal = signal
    
    def write(self, text):
        if text.strip():
            self.signal.new_log.emit(text.strip())
    
    def flush(self):
        pass


# Global main window reference
_main_window_instance = None

class MainWindow(QMainWindow):
    """Main window"""
    
    def __init__(self):
        super().__init__()
        global _main_window_instance
        _main_window_instance = self
        # Add this after initializing other components
        self.language_mgr = get_language_manager()
        self.language_mgr.register_callback(self.update_ui_text)

        self.setObjectName('MainWindow')
        
        self.setWindowTitle(tr("main_window_title"+" v"+str(VERSION)))
        self.setGeometry(100, 100, 900, 700)
        
        # Initialize components
        self.auto_clicker = get_auto_clicker()
        self.script_manager = get_script_manager()
        self.hotkey_mgr = get_hotkey_manager()
        self.vision = get_vision()
        self.macro_editor = get_macro_editor()
        
        # Set recording completion callback function
        self.script_manager.recorder.on_record_stopped = self.on_record_stopped
        
        # Log signal
        self.log_signal = LogSignal()
        self.log_signal.new_log.connect(self.append_log)
        
        # Set global log signal
        from core.logger import set_log_signal
        set_log_signal(self.log_signal)

        # Timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(500)
        
        self.init_ui()
        self.setup_menu()
        self.setup_statusbar()
        
        # Start hotkey management
        self.hotkey_mgr.start()

        logger.info("Main window initialization completed")
    
    def init_ui(self):
        """Initialize interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left: Function tabs
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        self.tab_widget = QTabWidget()
        left_layout.addWidget(self.tab_widget)
        
        # Add function tabs
        self.tab_widget.addTab(self.create_autoclick_tab(), tr("tab_autoclick"))
        self.tab_widget.addTab(self.create_recorder_tab(), tr("tab_recorder"))
        self.tab_widget.addTab(self.create_vision_tab(), tr("tab_vision"))
        self.tab_widget.addTab(self.create_macro_tab(), tr("tab_macro"))
        self.tab_widget.addTab(self.create_settings_tab(), tr("tab_settings"))
        
        splitter.addWidget(left_widget)
        
        # Right: Log window
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        log_group = QGroupBox("Runtime Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(1000)
        log_layout.addWidget(self.log_text)
        
        # Log buttons
        log_btn_layout = QHBoxLayout()
        
        self.clear_log_btn = QPushButton(tr("clear_log"))
        self.clear_log_btn.clicked.connect(self.clear_log)
        log_btn_layout.addWidget(self.clear_log_btn)
        
        self.save_log_btn = QPushButton(tr("save_log"))
        self.save_log_btn.clicked.connect(self.save_log)
        log_btn_layout.addWidget(self.save_log_btn)
        
        log_btn_layout.addStretch()
        log_layout.addLayout(log_btn_layout)
        
        right_layout.addWidget(log_group)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 300])
    
    def update_ui_text(self):
        """Update all UI text when language changes"""
        # Update window title
        self.setWindowTitle(tr("main_window_title"))
        
        # Update tab names
        self.tab_widget.setTabText(0, tr("tab_autoclick"))
        self.tab_widget.setTabText(1, tr("tab_recorder"))
        self.tab_widget.setTabText(2, tr("tab_vision"))
        self.tab_widget.setTabText(3, tr("tab_macro"))
        self.tab_widget.setTabText(4, tr("tab_settings"))
        
        # Update all UI elements using tr() function
        # Example: self.some_label.setText(tr("some_key"))

    def create_settings_tab(self) -> QWidget:
        """Create settings tab with language selection"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # General settings
        general_group = QGroupBox(tr("general_settings"))
        general_layout = QVBoxLayout(general_group)
        
        # Language selection
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel(tr("language") + ":"))
        
        self.language_combo = QComboBox()
        self.language_combo.addItem(tr("english"), Language.ENGLISH)
        self.language_combo.addItem(tr("chinese"), Language.CHINESE)
        lang_layout.addWidget(self.language_combo)
        
        self.apply_lang_btn = QPushButton(tr("apply"))
        self.apply_lang_btn.clicked.connect(self.apply_language_settings)
        lang_layout.addWidget(self.apply_lang_btn)
        
        lang_layout.addStretch()
        general_layout.addLayout(lang_layout)
        
        # Restart notice
        restart_label = QLabel(tr("restart_required"))
        restart_label.setStyleSheet("color: orange; font-size: 10px;")
        general_layout.addWidget(restart_label)
        
        layout.addWidget(general_group)
        layout.addStretch()
        
        return tab

    def apply_language_settings(self):
        """Apply language settings"""
        language = self.language_combo.currentData()
        self.language_mgr.set_language(language)

    def create_autoclick_tab(self) -> QWidget:
        """Create auto-clicker tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignTop)
        
        # Button selection
        btn_group = QGroupBox(tr("mouse_button"))
        btn_layout = QHBoxLayout(btn_group)
        
        self.click_button_combo = QComboBox()
        self.click_button_combo.addItems([tr("left_button"), tr("right_button"), tr("middle_button")])
        btn_layout.addWidget(self.click_button_combo)
        btn_layout.addStretch()
        
        layout.addWidget(btn_group)
        
        # Interval settings
        interval_group = QGroupBox(tr("click_interval"))
        interval_layout = QVBoxLayout(interval_group)
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel(tr("mode") + ":"))
        self.click_mode_combo = QComboBox()
        self.click_mode_combo.addItems([tr("fixed_interval"), tr("random_interval")])
        self.click_mode_combo.currentIndexChanged.connect(self.on_click_mode_changed)
        mode_layout.addWidget(self.click_mode_combo)
        mode_layout.addStretch()
        interval_layout.addLayout(mode_layout)
        
        # Fixed interval
        self.fixed_interval_widget = QWidget()
        self.fixed_interval_layout = QHBoxLayout(self.fixed_interval_widget)
        self.fixed_interval_layout.addWidget(QLabel(tr("interval_seconds") + ":"))
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.01, 10.0)
        self.interval_spin.setValue(0.1)
        self.interval_spin.setDecimals(2)
        self.interval_spin.setSingleStep(0.01)
        self.fixed_interval_layout.addWidget(self.interval_spin)
        self.fixed_interval_layout.addStretch()
        interval_layout.addWidget(self.fixed_interval_widget)
        
        # 随机间隔
        self.random_interval_widget = QWidget()
        self.random_interval_layout = QHBoxLayout(self.random_interval_widget)
        self.random_interval_layout.addWidget(QLabel(tr("min") + ":"))
        self.min_interval_spin = QDoubleSpinBox()
        self.min_interval_spin.setRange(0.01, 10.0)
        self.min_interval_spin.setValue(0.05)
        self.min_interval_spin.setDecimals(2)
        self.random_interval_layout.addWidget(self.min_interval_spin)
        
        self.random_interval_layout.addWidget(QLabel(tr("max") + ":"))
        self.max_interval_spin = QDoubleSpinBox()
        self.max_interval_spin.setRange(0.01, 10.0)
        self.max_interval_spin.setValue(0.15)
        self.max_interval_spin.setDecimals(2)
        self.random_interval_layout.addWidget(self.max_interval_spin)
        self.random_interval_layout.addStretch()
        interval_layout.addWidget(self.random_interval_widget)
        
        self.random_interval_widget.hide()
        
        layout.addWidget(interval_group)
        
        # 次数设置
        count_group = QGroupBox(tr("click_count"))
        count_layout = QHBoxLayout(count_group)
        
        self.infinite_check = QCheckBox(tr("infinite_click"))
        self.infinite_check.setChecked(True)
        self.infinite_check.stateChanged.connect(self.on_infinite_changed)
        count_layout.addWidget(self.infinite_check)
        
        count_layout.addWidget(QLabel(tr("click_count") + ":"))
        self.click_count_spin = QSpinBox()
        self.click_count_spin.setRange(1, 999999)
        self.click_count_spin.setValue(100)
        self.click_count_spin.setEnabled(False)
        count_layout.addWidget(self.click_count_spin)
        count_layout.addStretch()
        
        layout.addWidget(count_group)
        
        # 位置设置
        pos_group = QGroupBox(tr("click_position"))
        pos_layout = QVBoxLayout(pos_group)
        
        self.current_pos_check = QCheckBox(tr("use_current_mouse_position"))
        self.current_pos_check.setChecked(True)
        self.current_pos_check.stateChanged.connect(self.on_pos_mode_changed)
        pos_layout.addWidget(self.current_pos_check)
        
        self.fixed_pos_layout = QHBoxLayout()
        self.fixed_pos_layout.addWidget(QLabel("X:"))
        self.pos_x_spin = QSpinBox()
        self.pos_x_spin.setRange(0, 9999)
        self.fixed_pos_layout.addWidget(self.pos_x_spin)
        
        self.fixed_pos_layout.addWidget(QLabel("Y:"))
        self.pos_y_spin = QSpinBox()
        self.pos_y_spin.setRange(0, 9999)
        self.fixed_pos_layout.addWidget(self.pos_y_spin)
        
        self.pick_pos_btn = QPushButton(tr("pick_position"))
        self.pick_pos_btn.clicked.connect(self.pick_position)
        self.fixed_pos_layout.addWidget(self.pick_pos_btn)
        self.fixed_pos_layout.addStretch()
        
        pos_layout.addLayout(self.fixed_pos_layout)
        self.fixed_pos_layout.setEnabled(False)
        
        layout.addWidget(pos_group)
        
        # 热键设置
        hotkey_group = QGroupBox(tr("hotkeys"))
        hotkey_layout = QHBoxLayout(hotkey_group)
        
        hotkey_layout.addWidget(QLabel(tr("start_stop_hotkey") + ":"))
        self.click_hotkey_edit = QLineEdit("F8")
        self.click_hotkey_edit.setMaximumWidth(80)
        hotkey_layout.addWidget(self.click_hotkey_edit)
        
        self.hold_mode_check = QCheckBox(tr("hold_mode"))
        self.hold_mode_check.setChecked(True)
        hotkey_layout.addWidget(self.hold_mode_check)
        hotkey_layout.addStretch()
        
        layout.addWidget(hotkey_group)
        
        # 人性化设置
        humanize_group = QGroupBox(tr("humanized_simulation"))
        humanize_layout = QVBoxLayout(humanize_group)
        
        self.humanize_check = QCheckBox(tr("enable_humanized_simulation")) 
        self.humanize_check.setChecked(True)
        humanize_layout.addWidget(self.humanize_check)
        
        offset_layout = QHBoxLayout()
        offset_layout.addWidget(QLabel(tr("click_offset_pixels") + ": (px)"))
        self.offset_spin = QSpinBox()
        self.offset_spin.setRange(0, 20)
        self.offset_spin.setValue(3)
        offset_layout.addWidget(self.offset_spin)
        offset_layout.addStretch()
        humanize_layout.addLayout(offset_layout)
        
        layout.addWidget(humanize_group)
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        
        self.start_click_btn = QPushButton(tr("start_autoclick_hotkey"))
        self.start_click_btn.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px; padding: 10px;")
        self.start_click_btn.clicked.connect(self.toggle_autoclick)
        btn_layout.addWidget(self.start_click_btn)
        
        self.stop_click_btn = QPushButton(tr("stop_autoclick"))
        self.stop_click_btn.setStyleSheet("background-color: #f44336; color: white; font-size: 14px; padding: 10px;")
        self.stop_click_btn.clicked.connect(self.stop_autoclick)
        self.stop_click_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_click_btn)
        
        layout.addLayout(btn_layout)
        
        # 状态显示
        self.click_status_label = QLabel(tr("status") + ": " + tr("stopped"))
        self.click_status_label.setStyleSheet("color: gray; font-weight: bold;")
        layout.addWidget(self.click_status_label)
        
        self.click_stats_label = QLabel(tr("click_count") + ": 0 | " + tr("runtime") + ": 0s | " + tr("cps") + ": 0")
        layout.addWidget(self.click_stats_label)
        
        layout.addStretch()
        
        return tab
    
    def create_recorder_tab(self) -> QWidget:
        """创建录制回放标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 录制控制
        record_group = QGroupBox(tr("recording_control"))
        record_layout = QHBoxLayout(record_group)
        
        self.start_record_btn = QPushButton(tr("start_recording_hotkey"))
        self.start_record_btn.setStyleSheet("background-color: #2196F3; color: white;")
        self.start_record_btn.clicked.connect(self.start_recording)
        record_layout.addWidget(self.start_record_btn)
        
        self.stop_record_btn = QPushButton(tr("stop_recording_hotkey"))
        self.stop_record_btn.setStyleSheet("background-color: #FF9800; color: white;")
        self.stop_record_btn.clicked.connect(self.stop_recording)
        self.stop_record_btn.setEnabled(False)
        record_layout.addWidget(self.stop_record_btn)
        
        record_layout.addStretch()
        layout.addWidget(record_group)
        
        # 回放控制
        play_group = QGroupBox(tr("playback_control"))
        play_layout = QHBoxLayout(play_group)
        
        self.play_script_btn = QPushButton(tr("play_script_hotkey"))
        self.play_script_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.play_script_btn.clicked.connect(self.play_script)
        play_layout.addWidget(self.play_script_btn)
        
        self.stop_script_btn = QPushButton(tr("stop_script_hotkey"))
        self.stop_script_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.stop_script_btn.clicked.connect(self.stop_script)
        play_layout.addWidget(self.stop_script_btn)
        
        play_layout.addWidget(QLabel(tr("loop") + ":"))
        self.loop_spin = QSpinBox()
        self.loop_spin.setRange(1, 999)
        self.loop_spin.setValue(1)
        play_layout.addWidget(self.loop_spin)
        
        play_layout.addStretch()
        layout.addWidget(play_group)
        
        # 脚本列表
        script_group = QGroupBox(tr("script_list"))
        script_layout = QVBoxLayout(script_group)
        
        self.script_list = QListWidget()
        self.script_list.itemClicked.connect(self.on_script_selected)
        script_layout.addWidget(self.script_list)
        
        # 脚本操作按钮
        script_btn_layout = QHBoxLayout()
        
        self.load_script_btn = QPushButton(tr("load"))
        self.load_script_btn.clicked.connect(self.load_script)
        script_btn_layout.addWidget(self.load_script_btn)
        
        self.save_script_btn = QPushButton(tr("save"))
        self.save_script_btn.clicked.connect(self.save_script)
        script_btn_layout.addWidget(self.save_script_btn)
        
        self.rename_script_btn = QPushButton(tr("rename"))
        self.rename_script_btn.clicked.connect(self.rename_script)
        script_btn_layout.addWidget(self.rename_script_btn)
        
        self.delete_script_btn = QPushButton(tr("delete"))
        self.delete_script_btn.clicked.connect(self.delete_script)
        script_btn_layout.addWidget(self.delete_script_btn)
        
        script_btn_layout.addStretch()
        script_layout.addLayout(script_btn_layout)
        
        layout.addWidget(script_group)
        
        # 刷新脚本列表
        self.refresh_script_list()
        
        return tab
    
    def create_vision_tab(self) -> QWidget:
        """Create image recognition tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignTop)
        
        # Template matching
        match_group = QGroupBox(tr("template_match"))
        match_layout = QVBoxLayout(match_group)
        
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel(tr("template_image") + ":"))
        self.template_path_edit = QLineEdit()
        file_layout.addWidget(self.template_path_edit)
        
        self.browse_template_btn = QPushButton(tr("browse") + "...")
        self.browse_template_btn.clicked.connect(self.browse_template)
        file_layout.addWidget(self.browse_template_btn)
        match_layout.addLayout(file_layout)
        
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel(tr("threshold") + ":"))
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.1, 1.0)
        self.threshold_spin.setValue(0.8)
        self.threshold_spin.setDecimals(2)
        self.threshold_spin.setSingleStep(0.05)
        threshold_layout.addWidget(self.threshold_spin)
        threshold_layout.addStretch()
        match_layout.addLayout(threshold_layout)
        
        self.match_btn = QPushButton(tr("find_template"))
        self.match_btn.clicked.connect(self.find_template)
        match_layout.addWidget(self.match_btn)
        
        self.match_result_label = QLabel(tr("result") + ": "+tr("not_found"))
        match_layout.addWidget(self.match_result_label)
        
        layout.addWidget(match_group)
        
        # 颜色识别
        color_group = QGroupBox(tr("color_recognition"))
        color_layout = QVBoxLayout(color_group)
        
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("X:"))
        self.color_x_spin = QSpinBox()
        self.color_x_spin.setRange(0, 9999)
        pos_layout.addWidget(self.color_x_spin)
        
        pos_layout.addWidget(QLabel("Y:"))
        self.color_y_spin = QSpinBox()
        self.color_y_spin.setRange(0, 9999)
        pos_layout.addWidget(self.color_y_spin)
        
        self.pick_color_btn = QPushButton(tr("pick_color_position"))
        self.pick_color_btn.clicked.connect(self.pick_color_position)
        pos_layout.addWidget(self.pick_color_btn)
        
        self.get_color_btn = QPushButton(tr("get_color"))
        self.get_color_btn.clicked.connect(self.get_color)
        pos_layout.addWidget(self.get_color_btn)
        pos_layout.addStretch()
        
        color_layout.addLayout(pos_layout)
        
        self.color_result_label = QLabel(tr("color")+": "+tr("not_get"))
        color_layout.addWidget(self.color_result_label)
        
        layout.addWidget(color_group)
        
        # 截图
        screenshot_group = QGroupBox(tr("screenshot"))
        screenshot_layout = QHBoxLayout(screenshot_group)
        
        self.screenshot_btn = QPushButton(tr("screenshot_fullscreen"))
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        screenshot_layout.addWidget(self.screenshot_btn)
        
        screenshot_layout.addStretch()
        layout.addWidget(screenshot_group)
        
        layout.addStretch()
        
        return tab
    
    def create_macro_tab(self) -> QWidget:
        """创建宏编辑标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 动作列表
        self.macro_list = QListWidget()
        layout.addWidget(self.macro_list)
        
        # 动作控制按钮
        btn_layout = QHBoxLayout()
        
        self.add_move_btn = QPushButton(tr("add_move"))
        self.add_move_btn.clicked.connect(lambda: self.add_macro_action(MacroActionType.MOVE))
        btn_layout.addWidget(self.add_move_btn)
        
        self.add_click_btn = QPushButton(tr("add_click"))
        self.add_click_btn.clicked.connect(lambda: self.add_macro_action(MacroActionType.CLICK))
        btn_layout.addWidget(self.add_click_btn)
        
        self.add_delay_btn = QPushButton(tr("add_delay"))
        self.add_delay_btn.clicked.connect(lambda: self.add_macro_action(MacroActionType.DELAY))
        btn_layout.addWidget(self.add_delay_btn)
        
        self.add_find_btn = QPushButton(tr("add_find_image"))
        self.add_find_btn.clicked.connect(lambda: self.add_macro_action(MacroActionType.FIND_IMAGE))
        btn_layout.addWidget(self.add_find_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 宏控制
        control_layout = QHBoxLayout()
        
        self.run_macro_btn = QPushButton(tr("run_macro"))
        self.run_macro_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.run_macro_btn.clicked.connect(self.run_macro)
        control_layout.addWidget(self.run_macro_btn)
        
        self.stop_macro_btn = QPushButton(tr("stop_macro"))
        self.stop_macro_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.stop_macro_btn.clicked.connect(self.stop_macro)
        control_layout.addWidget(self.stop_macro_btn)
        
        self.save_macro_btn = QPushButton(tr("save_macro"))
        self.save_macro_btn.clicked.connect(self.save_macro)
        control_layout.addWidget(self.save_macro_btn)
        
        self.load_macro_btn = QPushButton(tr("load_macro"))
        self.load_macro_btn.clicked.connect(self.load_macro)
        control_layout.addWidget(self.load_macro_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        return tab
    
    def create_settings_tab(self) -> QWidget:
        """创建设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignTop)
        
        # 热键设置
        hotkey_group = QGroupBox(tr("global_hotkeys"))
        hotkey_layout = QFormLayout(hotkey_group)
        
        self.hotkey_f6_edit = QLineEdit("F6")
        hotkey_layout.addRow(tr("play_script") + ":", self.hotkey_f6_edit)
        
        self.hotkey_f7_edit = QLineEdit("F7")
        hotkey_layout.addRow(tr("stop_playback") + ":", self.hotkey_f7_edit)
        
        self.hotkey_f8_edit = QLineEdit("F8")
        hotkey_layout.addRow(tr("autoclicker") + ":", self.hotkey_f8_edit)
        
        self.hotkey_f9_edit = QLineEdit("F9")
        hotkey_layout.addRow(tr("start_recording") + ":", self.hotkey_f9_edit)
        
        self.hotkey_f10_edit = QLineEdit("F10")
        hotkey_layout.addRow(tr("stop_recording") + ":", self.hotkey_f10_edit)
        
        layout.addWidget(hotkey_group)
        
        # 人性化设置
        humanize_group = QGroupBox(tr("humanization_settings"))
        humanize_layout = QFormLayout(humanize_group)
        
        self.min_delay_spin = QDoubleSpinBox()
        self.min_delay_spin.setRange(0.001, 1.0)
        self.min_delay_spin.setValue(0.05)
        self.min_delay_spin.setDecimals(3)
        humanize_layout.addRow(tr("min_delay_seconds") + ":", self.min_delay_spin)
        
        self.max_delay_spin = QDoubleSpinBox()
        self.max_delay_spin.setRange(0.001, 1.0)
        self.max_delay_spin.setValue(0.15)
        self.max_delay_spin.setDecimals(3)
        humanize_layout.addRow(tr("max_delay_seconds") + ":", self.max_delay_spin)
        
        layout.addWidget(humanize_group)
        
        # 保存按钮
        self.save_settings_btn = QPushButton(tr("save_settings"))
        self.save_settings_btn.clicked.connect(self.save_settings)
        layout.addWidget(self.save_settings_btn)
        
        layout.addStretch()
        
        return tab
    
    def setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu(tr("file"))
        
        exit_action = QAction(tr("exit"), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu(tr("help"))
        
        about_action = QAction(tr("about"), self)   
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_statusbar(self):
        """设置状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage(tr("ready"))
    
    # ========== 连点器功能 ==========
    
    def on_click_mode_changed(self, index):
        """点击模式改变"""
        if index == 0:  # 固定间隔
            self.fixed_interval_widget.show()
            self.random_interval_widget.hide()
        else:  # 随机间隔
            self.fixed_interval_widget.hide()
            self.random_interval_widget.show()
    
    def on_infinite_changed(self, state):
        """无限点击选项改变"""
        self.click_count_spin.setEnabled(not state)
    
    def on_pos_mode_changed(self, state):
        """位置模式改变"""
        self.fixed_pos_layout.setEnabled(not state)
    
    def pick_position(self):
        """拾取位置"""
        import pyautogui
        x, y = pyautogui.position()
        self.pos_x_spin.setValue(x)
        self.pos_y_spin.setValue(y)
        logger.info(f"拾取位置: ({x}, {y})")
    
    def toggle_autoclick(self):
        """切换连点器状态"""
        if self.auto_clicker.running:
            self.stop_autoclick()
        else:
            self.start_autoclick()
    
    def start_autoclick(self):
        """开始连点"""
        # 构建配置
        config = ClickConfig()
        
        # 按钮
        btn_map = {0: ClickButton.LEFT, 1: ClickButton.RIGHT, 2: ClickButton.MIDDLE}
        config.button = btn_map[self.click_button_combo.currentIndex()]
        
        # 模式
        config.click_mode = ClickMode.FIXED if self.click_mode_combo.currentIndex() == 0 else ClickMode.RANDOM
        config.interval = self.interval_spin.value()
        config.min_interval = self.min_interval_spin.value()
        config.max_interval = self.max_interval_spin.value()
        
        # 次数
        config.click_count = 0 if self.infinite_check.isChecked() else self.click_count_spin.value()
        
        # 位置
        config.use_current_pos = self.current_pos_check.isChecked()
        config.fixed_x = self.pos_x_spin.value()
        config.fixed_y = self.pos_y_spin.value()
        
        # 热键
        config.toggle_hotkey = self.click_hotkey_edit.text().lower()
        config.hold_mode = self.hold_mode_check.isChecked()
        
        # 人性化
        config.humanize = self.humanize_check.isChecked()
        config.click_offset = self.offset_spin.value()
        
        # 更新配置
        self.auto_clicker.update_config(config)
        
        # 开始
        if self.auto_clicker.start():
            self.start_click_btn.setEnabled(False)
            self.stop_click_btn.setEnabled(True)
    
            self.click_status_label.setText(tr("status") + ": " + tr("status_running"))
            self.click_status_label.setStyleSheet("color: green; font-weight: bold;")

    def get_clicker_config(self):
        """获取当前连点器配置"""
        from core.auto_clicker import ClickConfig
        
        config = ClickConfig()
        
        # 模式
        config.click_mode = ClickMode.FIXED if self.click_mode_combo.currentIndex() == 0 else ClickMode.RANDOM
        config.interval = self.interval_spin.value()
        config.min_interval = self.min_interval_spin.value()
        config.max_interval = self.max_interval_spin.value()
        
        # 次数
        config.click_count = 0 if self.infinite_check.isChecked() else self.click_count_spin.value()
        
        # 位置
        config.use_current_pos = self.current_pos_check.isChecked()
        config.fixed_x = self.pos_x_spin.value()
        config.fixed_y = self.pos_y_spin.value()
        
        # 热键
        config.toggle_hotkey = self.click_hotkey_edit.text().lower()
        config.hold_mode = self.hold_mode_check.isChecked()
        
        # 人性化
        config.humanize = self.humanize_check.isChecked()
        config.click_offset = self.offset_spin.value()
        
        return config

    
    def stop_autoclick(self):
        """停止连点"""
        self.auto_clicker.stop()
        self.start_click_btn.setEnabled(True)
        self.stop_click_btn.setEnabled(False)
        self.click_status_label.setText(tr("status") + ": " + tr("status_stopped"))
        self.click_status_label.setStyleSheet("color: gray; font-weight: bold;")
    
    # ========== 录制回放功能 ==========
    
    def start_recording(self):
        """开始录制"""
        if self.script_manager.recorder.start_recording():
            self.start_record_btn.setEnabled(False)
            self.stop_record_btn.setEnabled(True)
            logger.info(tr("start_recording"))
    
    def on_record_stopped(self, actions):
        """录制完成回调（由热键触发）"""
        # 在主线程中执行保存操作
        #from PyQt5.QtCore import QTimer, pyqtSignal, QObject
        from core.logger import get_logger
        logger = get_logger()
        
        logger.debug(f"on_record_stopped is called, actions count: {len(actions) if actions else 0}")
        
        # 方法1：直接在主线程中执行（如果已经在主线程）
        try:
            logger.debug("try to call _handle_record_stopped")
            self._handle_record_stopped(actions)
            return
        except Exception as e:
            logger.debug(f"call _handle_record_stopped failed (maybe not in main thread): {e}")
        
        # 方法2：使用QTimer.singleShot（确保在主线程中执行）
        """def timer_callback():
            try:
                logger.debug("QTimer回调执行")
                self._handle_record_stopped(actions)
            except Exception as e:
                logger.error(f"QTimer回调执行失败: {e}")
        
        # 使用更长的延迟确保在主线程中执行
        QTimer.singleShot(100, timer_callback)
        logger.debug("已安排QTimer回调")"""
    
    def _handle_record_stopped(self, actions):
        """处理录制完成（在主线程中执行）"""
        self.start_record_btn.setEnabled(True)
        self.stop_record_btn.setEnabled(False)
        
        if actions:
            # 保存对话框
            filename, ok = QFileDialog.getSaveFileName(
                self, tr("save_script"), "scripts/recording.json", "JSON Files (*.json)"
            )
            if ok:
                self.script_manager.recorder.save_to_json(filename)
                self.refresh_script_list()
    
    def stop_recording(self):
        """停止录制（由界面按钮触发）"""
        actions = self.script_manager.recorder.stop_recording()
        self.start_record_btn.setEnabled(True)
        self.stop_record_btn.setEnabled(False)
        
        """if actions:
            # 保存对话框
            filename, ok = QFileDialog.getSaveFileName(
                self, tr("save_script"), "scripts/recording.json", "JSON Files (*.json)"
            )
            if ok:
                self.script_manager.recorder.save_to_json(filename)
                self.refresh_script_list()"""
    
    def play_script(self):
        """播放脚本"""
        loop_count = self.loop_spin.value()
        if self.script_manager.player.play(loop_count):
            logger.info(f"{tr('play_script')} loop {loop_count}")
    
    def stop_script(self):
        """停止脚本"""
        self.script_manager.player.stop()
    
    def refresh_script_list(self):
        """刷新脚本列表"""
        self.script_list.clear()
        scripts = self.script_manager.get_script_list()
        for script in scripts:
            item = QListWidgetItem(script['name'])
            item.setData(Qt.UserRole, script['path'])
            self.script_list.addItem(item)
    
    def on_script_selected(self, item):
        """脚本选中"""
        path = item.data(Qt.UserRole)
        self.script_manager.player.load_from_file(path)
        logger.info(f"{tr('script_loaded')}: {item.text()}")
    
    def load_script(self):
        """加载脚本"""
        filename, _ = QFileDialog.getOpenFileName(
            self, tr("load_script"), "scripts", "JSON Files (*.json)"
        )
        if filename:
            self.script_manager.player.load_from_file(filename)
            logger.info(f"{tr('script_loaded')}: {filename}")
    
    def save_script(self):
        """保存脚本"""
        # 保存当前录制的脚本
        filename, ok = QFileDialog.getSaveFileName(
            self, tr("save_script"), "scripts/script.json", "JSON Files (*.json)"
        )
        if ok:
            self.script_manager.recorder.save_to_json(filename)
            self.refresh_script_list()
    
    def rename_script(self):
        """重命名脚本"""
        item = self.script_list.currentItem()
        if not item:
            QMessageBox.warning(self, tr("warning"), tr("choose_a_script"))
            return
        
        old_name = item.text()
        from PyQt5.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(self, tr("rename"), tr("new_name"), text=old_name)
        if ok and new_name:
            if self.script_manager.rename_script(old_name, new_name):
                self.refresh_script_list()
    
    def delete_script(self):
        """删除脚本"""
        item = self.script_list.currentItem()
        if not item:
            QMessageBox.warning(self, tr("warning"), tr("choose_a_script"))
            return
        
        reply = QMessageBox.question(
            self, tr("confirm"), f"{tr('confirm_delete_script')}{item.text()}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.script_manager.delete_script(item.text())
            self.refresh_script_list()
    
    # ========== 图像识别功能 ==========
    
    def browse_template(self):
        """浏览模板文件"""
        filename, _ = QFileDialog.getOpenFileName(
            self, tr("select_template_image"), "images", "Images (*.png *.jpg *.bmp)"
        )
        if filename:
            self.template_path_edit.setText(filename)
    
    def find_template(self):
        """查找模板"""
        template_path = self.template_path_edit.text()
        if not template_path:
            QMessageBox.warning(self, tr("warning"), tr("select_template_image"))
            return
        
        threshold = self.threshold_spin.value()
        result = self.vision.find_template(template_path, threshold=threshold,multi_scale=False)
        
        if result.found:
            self.match_result_label.setText(
                f"{tr('result')}: {tr('found')}! {tr('position')}: ({result.x}, {result.y}), {tr('sim_threshold')}: {result.confidence:.3f}"
            )
            self.match_result_label.setStyleSheet("color: green;")
        else:
            self.match_result_label.setText(tr("result") + " " + tr("not_found"))
            self.match_result_label.setStyleSheet("color: red;")
    
    def pick_color_position(self):
        """拾取颜色位置"""
        import pyautogui
        x, y = pyautogui.position()
        self.color_x_spin.setValue(x)
        self.color_y_spin.setValue(y)
    
    def get_color(self):
        """获取颜色"""
        x = self.color_x_spin.value()
        y = self.color_y_spin.value()
        
        color_info = self.vision.get_pixel_color(x, y)
        self.color_result_label.setText(
            f"{tr('color')}: {color_info.hex} (R:{color_info.r}, G:{color_info.g}, B:{color_info.b})"
        )
    
    def take_screenshot(self):
        """截图"""
        import pyautogui
        from datetime import datetime
        
        screenshot = pyautogui.screenshot()
        filename = f"screenshots/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        screenshot.save(filename)
        logger.info(f"screenshot saved: {filename}")
        QMessageBox.information(self, tr("screenshot"), f"{tr('screenshot_saved')}: {filename}")
    
    # ========== 宏功能 ==========
    
    def add_macro_action(self, action_type: MacroActionType):
        """添加宏动作"""
        if action_type == MacroActionType.FIND_IMAGE:
            # 对于查找图像动作，弹出模板选择对话框
            self._add_find_image_action()
        else:
            action = MacroAction(action_type=action_type.value)
            self.macro_editor.add_action(action)
            self.refresh_macro_list()

    def _add_find_image_action(self):
        """添加查找图像动作 - 弹出模板选择对话框"""
        import os
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                    QListWidget, QListWidgetItem, QPushButton, 
                                    QDoubleSpinBox, QLineEdit, QMessageBox)
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtCore import Qt
        
        # 获取images目录下的所有图片文件
        images_dir = "images"
        if not os.path.exists(images_dir):
            os.makedirs(images_dir, exist_ok=True)
        
        # 支持的图片格式
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']
        image_files = []
        
        for file in os.listdir(images_dir):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_files.append(file)
        
        if not image_files:
            QMessageBox.warning(self, tr("warning"), tr("no_images_found"))
            return
        
        # 创建选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("select_template_image"))
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)
        
        layout = QVBoxLayout(dialog)
        
        # 图片列表
        label = QLabel(tr("select_template_image_prompt"))
        layout.addWidget(label)
        
        image_list = QListWidget()
        for image_file in image_files:
            item = QListWidgetItem(image_file)
            image_list.addItem(item)
        layout.addWidget(image_list)
        
        # 预览区域
        preview_label = QLabel(tr("preview"+":"))
        layout.addWidget(preview_label)
        
        preview_pixmap = QLabel()
        preview_pixmap.setMinimumSize(200, 150)
        preview_pixmap.setAlignment(Qt.AlignCenter)
        preview_pixmap.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        layout.addWidget(preview_pixmap)
        
        # 阈值设置
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel(tr("sim_threshold"+":"))
        threshold_layout.addWidget(threshold_label)
        
        threshold_spin = QDoubleSpinBox()
        threshold_spin.setRange(0.1, 1.0)
        threshold_spin.setValue(0.8)
        threshold_spin.setSingleStep(0.05)
        threshold_spin.setToolTip(tr("sim_threshold_prompt"))
        threshold_layout.addWidget(threshold_spin)
        threshold_layout.addStretch()
        layout.addLayout(threshold_layout)
        
        # 变量名设置
        var_layout = QHBoxLayout()
        var_label = QLabel(tr("save_to_var"+":"))
        var_layout.addWidget(var_label)
        
        var_edit = QLineEdit("found")
        var_edit.setPlaceholderText(tr("var_name"))
        var_edit.setToolTip(tr("var_name_prompt"))
        var_layout.addWidget(var_edit)
        var_layout.addStretch()
        layout.addLayout(var_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton(tr("ok"))
        cancel_btn = QPushButton(tr("cancel"))
        
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # 预览功能
        def update_preview():
            current_item = image_list.currentItem()
            if current_item:
                image_path = os.path.join(images_dir, current_item.text())
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # 缩放预览图
                    scaled_pixmap = pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    preview_pixmap.setPixmap(scaled_pixmap)
                else:
                    preview_pixmap.setText(tr("preview_failed"))
            else:
                preview_pixmap.setText(tr("no_preview"))
        
        image_list.currentItemChanged.connect(update_preview)
        
        # 按钮事件
        def on_ok():
            current_item = image_list.currentItem()
            if not current_item:
                QMessageBox.warning(dialog, tr("warning"), tr("select_image_prompt"))
                return
            
            image_path = os.path.join(images_dir, current_item.text())
            threshold = threshold_spin.value()
            save_to_var = var_edit.text().strip() or "found"
            
            # 创建查找图像动作
            action = MacroAction(
                action_type=MacroActionType.FIND_IMAGE.value,
                params={
                    'image_path': image_path,
                    'threshold': threshold,
                    'save_to_var': save_to_var
                }
            )
            
            self.macro_editor.add_action(action)
            self.refresh_macro_list()
            dialog.accept()
        
        def on_cancel():
            dialog.reject()
        
        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(on_cancel)
        
        # 初始预览
        if image_list.count() > 0:
            image_list.setCurrentRow(0)
        
        dialog.exec_()

    def refresh_macro_list(self):
        """刷新宏列表"""
        self.macro_list.clear()
        for action in self.macro_editor.get_actions():
            if action.action_type == MacroActionType.FIND_IMAGE.value:
                # 显示查找图像动作的详细信息
                image_path = action.params.get('image_path', '')
                threshold = action.params.get('threshold', 0.8)
                var_name = action.params.get('save_to_var', 'found')
                image_name = os.path.basename(image_path) if image_path else tr("unknown_image")
                item_text = f"match_image: {image_name} (threshold: {threshold}, var: {var_name})"
            else:
                item_text = f"{action.action_type} - {action.params}"

            self.macro_list.addItem(item_text)
    
    def run_macro(self):
        """运行宏"""
        if self.macro_editor.execute():
            logger.info("开始执行宏")
    
    def stop_macro(self):
        """停止宏"""
        self.macro_editor.stop()
    
    def save_macro(self):
        """保存宏"""
        filename, ok = QFileDialog.getSaveFileName(
            self, tr("save_macro"), "scripts/macro.json", "JSON Files (*.json)"
        )
        if ok:
            name = Path(filename).stem
            self.macro_editor.save(name)
    
    def load_macro(self):
        """加载宏"""
        filename, _ = QFileDialog.getOpenFileName(
            self, tr("load_macro"), "scripts", "JSON Files (*.json)"
        )
        if filename:
            name = Path(filename).stem
            self.macro_editor.load(name)
            self.refresh_macro_list()
    
    # ========== 设置功能 ==========
    
    def save_settings(self):
        """保存设置"""
        # TODO: 实现设置保存
        QMessageBox.information(self, tr("settings"), tr("settings_saved"))
    
    # ========== 日志功能 ==========
    
    def append_log(self, text):
        """追加日志"""
        #self.log_text.append(text)

        """插入日志到顶部（最新的消息在最上面）"""
        # 获取当前文本
        current_text = self.log_text.toPlainText()
        
        # 添加时间戳
        from datetime import datetime
        timestamp = datetime.now().strftime("[%H:%M:%S] ")
        new_line = timestamp + text + "\n"
        
        # 将新消息插入到开头
        if current_text:
            new_text = new_line + current_text
        else:
            new_text = new_line
        
        # 设置新文本
        self.log_text.setPlainText(new_text)
        
        # 保持滚动到顶部（显示最新消息）
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.log_text.setTextCursor(cursor)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
    
    def save_log(self):
        """保存日志"""
        filename, _ = QFileDialog.getSaveFileName(
            self, tr("save_log"), "logs/log.txt", "Text Files (*.txt)"
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
    
    # ========== 状态更新 ==========
    
    def update_status(self):
        """更新状态"""
        # 更新连点器状态
        if self.auto_clicker.running:
            stats = self.auto_clicker.get_stats()
            self.click_stats_label.setText(
                f"{tr('click_count')}: {stats['total_clicks']} | "
                f"{tr('runtime')}: {stats['elapsed_time']:.1f}s | "
                f"{tr('cps')}: {stats['cps']:.1f}"
            )
    
    # ========== 其他 ==========
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, tr("about"),
            "<h2>" + tr("main_window_title") + " v" + str(VERSION) + "</h2>"
            "<p>" + tr("description") + "</p>"
            "<p>" + tr("features") + "</p>"
        )
    
    def closeEvent(self, event):
        """关闭事件"""
        self.auto_clicker.cleanup()
        self.hotkey_mgr.stop()
        logger.info("应用程序关闭")
        event.accept()


# 导入QFormLayout
from PyQt5.QtWidgets import QFormLayout


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()