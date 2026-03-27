"""
图像识别模块 - 提供图像模板匹配、OCR、颜色识别等功能
"""

import os
import cv2
import numpy as np
import pyautogui
from PIL import Image
from typing import Tuple, Optional, List, Dict, Union
from dataclasses import dataclass
from pathlib import Path
import time
import threading

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from .logger import get_logger

logger = get_logger()


@dataclass
class MatchResult:
    """匹配结果"""
    found: bool
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    confidence: float = 0.0
    scale: float = 1.0


@dataclass
class ColorInfo:
    """颜色信息"""
    r: int
    g: int
    b: int
    hex: str = ""
    
    def __post_init__(self):
        if not self.hex:
            self.hex = f"#{self.r:02x}{self.g:02x}{self.b:02x}"


class Vision:
    """图像识别器"""
    
    def __init__(self):
        self.template_cache: Dict[str, np.ndarray] = {}
        self.monitor_threads: Dict[str, threading.Thread] = {}
        self.monitor_running: Dict[str, bool] = {}
        
        # 设置Tesseract路径（如果可用）
        if TESSERACT_AVAILABLE:
            # 尝试常见安装路径
            tesseract_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
            for path in tesseract_paths:
                if Path(path).exists():
                    pytesseract.pytesseract.tesseract_cmd = path
                    logger.info(f"Tesseract路径设置: {path}")
                    break
        
        logger.info("Vision module initialized")
    
    def capture_screen(
        self, 
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> np.ndarray:
        """
        截取屏幕
        
        Args:
            region: 区域 (x, y, width, height)，None则全屏
            
        Returns:
            OpenCV格式的图像 (BGR)
        """
        screenshot = pyautogui.screenshot(region=region)
        # PIL转OpenCV (RGB -> BGR)
        image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        return image
    
    def load_template(self, template_path: str) -> Optional[np.ndarray]:
        """
        Load template image
        
        Args:
            template_path: Template image path
            
        Returns:
            OpenCV format image
        """
        # Check cache
        if template_path in self.template_cache:
            return self.template_cache[template_path]
        
        try:
            # Check if file exists
            if not os.path.exists(template_path):
                logger.error(f"Error: File does not exist - {template_path}")
                return None
    
            template = cv2.imread(template_path)
            if template is None:
                logger.error(f"Unable to load template: {template_path}")
                return None
            
            self.template_cache[template_path] = template
            logger.debug(f"Template loaded successfully: {template_path}")
            return template
            
        except Exception as e:
            logger.error(f"Failed to load template {template_path}: {e}")
            return None
    
    def clear_template_cache(self):
        """Clear template cache"""
        self.template_cache.clear()
        logger.info("Template cache cleared")
    
    def find_template(
        self,
        template_path: str,
        screen: Optional[np.ndarray] = None,
        region: Optional[Tuple[int, int, int, int]] = None,
        threshold: float = 0.8,
        multi_scale: bool = True,
        scale_range: Tuple[float, float] = (0.5, 1.5),
        scale_steps: int = 10
    ) -> MatchResult:
        """
        在屏幕上查找模板
        
        Args:
            template_path: 模板图像路径
            screen: 屏幕图像，None则自动截取
            region: 搜索区域
            threshold: 相似度阈值
            multi_scale: 是否多尺度匹配
            scale_range: 缩放范围
            scale_steps: 缩放步数
            
        Returns:
            匹配结果
        """
        # 加载模板
        template = self.load_template(template_path)
        if template is None:
            return MatchResult(found=False)
        
        # 获取屏幕图像
        if screen is None:
            # 如果region为None，使用全屏区域
            if region is None:
                # 获取屏幕尺寸作为全屏区域
                import pyautogui
                screen_width, screen_height = pyautogui.size()
                region = (0, 0, screen_width, screen_height)
            screen = self.capture_screen(region)
        
        template_h, template_w = template.shape[:2]
        
        best_match = MatchResult(found=False)
        
        if multi_scale:
            # 多尺度匹配
            scales = np.linspace(scale_range[0], scale_range[1], scale_steps)
            
            for scale in scales:
                # 缩放模板
                resized_template = cv2.resize(
                    template, 
                    None, 
                    fx=scale, 
                    fy=scale,
                    interpolation=cv2.INTER_AREA
                )
                
                # 模板匹配
                result = cv2.matchTemplate(screen, resized_template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_match.confidence and max_val >= threshold:
                    best_match = MatchResult(
                        found=True,
                        x=max_loc[0],
                        y=max_loc[1],
                        width=int(template_w * scale),
                        height=int(template_h * scale),
                        confidence=max_val,
                        scale=scale
                    )
        else:
            # 单尺度匹配
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                best_match = MatchResult(
                    found=True,
                    x=max_loc[0],
                    y=max_loc[1],
                    width=template_w,
                    height=template_h,
                    confidence=max_val,
                    scale=1.0
                )
        
        # 如果指定了区域，转换坐标
        if region and best_match.found:
            best_match.x += region[0]
            best_match.y += region[1]
        
        logger.debug(f"模板匹配: {template_path}, 结果: {best_match.found}, 置信度: {best_match.confidence:.3f}")
        
        return best_match
    
    def find_all_templates(
        self,
        template_path: str,
        screen: Optional[np.ndarray] = None,
        region: Optional[Tuple[int, int, int, int]] = None,
        threshold: float = 0.8,
        max_results: int = 10
    ) -> List[MatchResult]:
        """
        查找所有匹配的模板位置
        
        Args:
            template_path: 模板图像路径
            screen: 屏幕图像
            region: 搜索区域
            threshold: 相似度阈值
            max_results: 最大结果数
            
        Returns:
            匹配结果列表
        """
        template = self.load_template(template_path)
        if template is None:
            return []
        
        if screen is None:
            screen = self.capture_screen(region)
        
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        
        # 获取所有匹配位置
        locations = np.where(result >= threshold)
        
        matches = []
        template_h, template_w = template.shape[:2]
        
        for pt in zip(*locations[::-1]):
            # 检查是否与其他结果重叠
            is_new = True
            for match in matches:
                if (abs(match.x - pt[0]) < template_w // 2 and 
                    abs(match.y - pt[1]) < template_h // 2):
                    is_new = False
                    break
            
            if is_new:
                matches.append(MatchResult(
                    found=True,
                    x=pt[0] + (region[0] if region else 0),
                    y=pt[1] + (region[1] if region else 0),
                    width=template_w,
                    height=template_h,
                    confidence=float(result[pt[1], pt[0]]),
                    scale=1.0
                ))
                
                if len(matches) >= max_results:
                    break
        
        logger.debug(f"Found {len(matches)} matches")
        return matches
    
    def get_pixel_color(
        self, 
        x: int, 
        y: int,
        screen: Optional[np.ndarray] = None
    ) -> ColorInfo:
        """
        获取指定坐标的像素颜色
        
        Args:
            x: X坐标
            y: Y坐标
            screen: 屏幕图像
            
        Returns:
            颜色信息
        """
        if screen is None:
            screen = self.capture_screen()
        
        # OpenCV使用BGR格式
        b, g, r = screen[y, x]
        
        return ColorInfo(r=int(r), g=int(g), b=int(b))
    
    def wait_for_template(
        self,
        template_path: str,
        timeout: float = 10.0,
        check_interval: float = 0.5,
        region: Optional[Tuple[int, int, int, int]] = None,
        threshold: float = 0.8
    ) -> MatchResult:
        """
        等待模板出现
        
        Args:
            template_path: 模板路径
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）
            region: 搜索区域
            threshold: 相似度阈值
            
        Returns:
            匹配结果
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.find_template(template_path, region=region, threshold=threshold)
            if result.found:
                logger.info(f"template found: {template_path}")
                return result
            
            time.sleep(check_interval)
        
        logger.warning(f"template not found within timeout: {template_path}")
        return MatchResult(found=False)
    
    def start_monitor(
        self,
        monitor_id: str,
        template_path: str,
        callback: callable,
        check_interval: float = 1.0,
        region: Optional[Tuple[int, int, int, int]] = None,
        threshold: float = 0.8
    ):
        """
        启动区域监控
        
        Args:
            monitor_id: 监控ID
            template_path: 要监控的模板
            callback: 发现模板时的回调函数
            check_interval: 检查间隔
            region: 监控区域
            threshold: 相似度阈值
        """
        if monitor_id in self.monitor_threads and self.monitor_threads[monitor_id].is_alive():
            logger.warning(f"monitor {monitor_id} is already running")
            return
        
        self.monitor_running[monitor_id] = True
        
        def monitor_loop():
            while self.monitor_running.get(monitor_id, False):
                try:
                    result = self.find_template(
                        template_path,
                        region=region,
                        threshold=threshold
                    )
                    
                    if result.found:
                        callback(result)
                    
                    time.sleep(check_interval)
                    
                except Exception as e:
                    logger.error(f"monitor {monitor_id} error: {e}")
                    time.sleep(check_interval)
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        self.monitor_threads[monitor_id] = thread
        
        logger.info(f"monitor started: {monitor_id}")
    
    def stop_monitor(self, monitor_id: str):
        """停止区域监控"""
        self.monitor_running[monitor_id] = False
        logger.info(f"monitor stopped: {monitor_id}")
    
    def stop_all_monitors(self):
        """停止所有监控"""
        for monitor_id in list(self.monitor_running.keys()):
            self.stop_monitor(monitor_id)
        logger.info(f"all monitors stopped")
    
    def ocr(
        self,
        region: Optional[Tuple[int, int, int, int]] = None,
        image: Optional[np.ndarray] = None,
        lang: str = 'chi_sim+eng'
    ) -> str:
        """
        OCR文字识别
        
        Args:
            region: 识别区域
            image: 图像，None则自动截图
            lang: 语言
            
        Returns:
            识别到的文字
        """
        if not TESSERACT_AVAILABLE:
            logger.error("Tesseract is not installed, cannot perform OCR recognition")
            return ""
        
        try:
            if image is None:
                screenshot = pyautogui.screenshot(region=region)
                image = np.array(screenshot)
            
            # 转换为PIL Image
            pil_image = Image.fromarray(image)
            
            # OCR识别
            text = pytesseract.image_to_string(pil_image, lang=lang)
            
            logger.debug(f"OCR recognition result: {text[:50]}...")
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR recognition failed: {e}")
            return ""
    
    def draw_rectangle(
        self,
        image: np.ndarray,
        x: int,
        y: int,
        width: int,
        height: int,
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> np.ndarray:
        """
        在图像上绘制矩形框
        
        Args:
            image: 图像
            x, y: 左上角坐标
            width, height: 宽高
            color: BGR颜色
            thickness: 线宽
            
        Returns:
            绘制后的图像
        """
        result = image.copy()
        cv2.rectangle(result, (x, y), (x + width, y + height), color, thickness)
        return result
    
    def highlight_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        duration: float = 1.0,
        color: Tuple[int, int, int] = (0, 255, 0)
    ):
        """
        在屏幕上高亮显示区域（调试用）
        
        Args:
            x, y: 左上角坐标
            width, height: 宽高
            duration: 显示时长
            color: BGR颜色
        """
        try:
            import tkinter as tk
            
            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes('-topmost', True)
            root.attributes('-transparentcolor', 'white')
            root.geometry(f"{width}x{height}+{x}+{y}")
            
            canvas = tk.Canvas(root, width=width, height=height, bg='white', highlightthickness=0)
            canvas.pack()
            
            # 绘制边框
            canvas.create_rectangle(2, 2, width-2, height-2, outline='#00ff00', width=3)
            
            root.after(int(duration * 1000), root.destroy)
            root.mainloop()
            
        except Exception as e:
            logger.error(f"highlight region failed, error: {e}")


# 全局图像识别实例
vision = Vision()


def get_vision() -> Vision:
    """获取图像识别实例"""
    return vision