"""
Humanization Simulation Module - Simulates human operation behavior
Provides random delays, click offsets, smooth movement, and other functions
"""

import random
import time
import math
from typing import Tuple, Optional, List
import numpy as np
from dataclasses import dataclass

from .logger import get_logger

logger = get_logger()


@dataclass
class HumanizeConfig:
    """Humanization configuration"""
    # Random delays
    min_delay: float = 0.05  # Minimum delay (seconds)
    max_delay: float = 0.15  # Maximum delay (seconds)
    
    # Click offsets
    click_offset_radius: int = 3  # Click offset radius (pixels)
    
    # Smooth movement
    move_duration_min: float = 0.2  # Minimum movement duration
    move_duration_max: float = 0.5  # Maximum movement duration
    bezier_control_points: int = 4  # Number of Bezier curve control points
    
    # Random jitter
    jitter_enabled: bool = True
    jitter_amount: int = 2  # Jitter amount
    
    # Behavior statistics
    track_statistics: bool = True


class Humanizer:
    """Humanized operation simulator"""
    
    def __init__(self, config: Optional[HumanizeConfig] = None):
        self.config = config or HumanizeConfig()
        self.stats = {
            'total_clicks': 0,
            'total_moves': 0,
            'total_delays': 0,
            'avg_click_frequency': 0,
            'last_click_time': 0
        }
        self.click_times: List[float] = []
    
    def random_delay(self, base_delay: float = 0.0) -> float:
        """
        Add random delay
        
        Args:
            base_delay: Base delay time
            
        Returns:
            Actual delay time
        """
        random_delay = random.uniform(self.config.min_delay, self.config.max_delay)
        total_delay = base_delay + random_delay
        
        time.sleep(total_delay)
        
        self.stats['total_delays'] += 1
        logger.debug(f"Random delay: {total_delay:.3f}s")
        
        return total_delay
    
    def get_click_offset(self, x: int, y: int) -> Tuple[int, int]:
        """
        Get click coordinates with offset
        
        Args:
            x: Original X coordinate
            y: Original Y coordinate
            
        Returns:
            Offset coordinates (x, y)
        """
        if self.config.click_offset_radius <= 0:
            return x, y
        
        # Use Gaussian distribution to make offsets more concentrated in the center
        offset_x = int(random.gauss(0, self.config.click_offset_radius / 2))
        offset_y = int(random.gauss(0, self.config.click_offset_radius / 2))
        
        # Limit within radius range
        offset_x = max(-self.config.click_offset_radius, min(self.config.click_offset_radius, offset_x))
        offset_y = max(-self.config.click_offset_radius, min(self.config.click_offset_radius, offset_y))
        
        new_x = x + offset_x
        new_y = y + offset_y
        
        logger.debug(f"Click offset: ({x}, {y}) -> ({new_x}, {new_y})")
        
        return new_x, new_y
    
    def generate_bezier_curve(
        self, 
        start: Tuple[int, int], 
        end: Tuple[int, int],
        control_points: Optional[List[Tuple[int, int]]] = None
    ) -> List[Tuple[int, int]]:
        """
        Generate Bezier curve path
        
        Args:
            start: Start point coordinates
            end: End point coordinates
            control_points: Control points list, automatically generated if None
            
        Returns:
            Path points list
        """
        if control_points is None:
            # Generate random control points
            control_points = self._generate_control_points(start, end)
        
        # Build all points
        points = [start] + control_points + [end]
        n = len(points) - 1
        
        # Generate curve points
        curve_points = []
        steps = max(20, int(math.dist(start, end) / 5))  # Dynamically adjust steps based on distance
        
        for t in np.linspace(0, 1, steps):
            point = self._bezier_point(points, n, t)
            curve_points.append((int(point[0]), int(point[1])))
        
        # Add jitter
        if self.config.jitter_enabled:
            curve_points = self._add_jitter(curve_points)
        
        return curve_points
    
    def _generate_control_points(
        self, 
        start: Tuple[int, int], 
        end: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """Generate random control points"""
        control_points = []
        
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        # Generate number of control points based on distance
        num_points = min(self.config.bezier_control_points, max(2, int(distance / 100)))
        
        for i in range(num_points):
            t = (i + 1) / (num_points + 1)
            
            # Base position
            base_x = start[0] + dx * t
            base_y = start[1] + dy * t
            
            # Add random offset (perpendicular to movement direction)
            offset_range = distance * 0.2 * random.uniform(0.5, 1.5)
            angle = math.atan2(dy, dx) + math.pi / 2
            
            offset_x = math.cos(angle) * offset_range * random.uniform(-1, 1)
            offset_y = math.sin(angle) * offset_range * random.uniform(-1, 1)
            
            control_points.append((int(base_x + offset_x), int(base_y + offset_y)))
        
        return control_points
    
    def _bezier_point(
        self, 
        points: List[Tuple[int, int]], 
        n: int, 
        t: float
    ) -> Tuple[float, float]:
        """Calculate point on Bezier curve (de Casteljau's algorithm)"""
        if n == 0:
            return points[0]
        
        new_points = []
        for i in range(n):
            x = (1 - t) * points[i][0] + t * points[i + 1][0]
            y = (1 - t) * points[i][1] + t * points[i + 1][1]
            new_points.append((x, y))
        
        return self._bezier_point(new_points, n - 1, t)
    
    def _add_jitter(self, points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Add random jitter to path"""
        if not self.config.jitter_enabled or self.config.jitter_amount <= 0:
            return points
        
        jittered = []
        for x, y in points:
            jitter_x = random.randint(-self.config.jitter_amount, self.config.jitter_amount)
            jitter_y = random.randint(-self.config.jitter_amount, self.config.jitter_amount)
            jittered.append((x + jitter_x, y + jitter_y))
        
        return jittered
    
    def smooth_move(
        self, 
        start: Tuple[int, int], 
        end: Tuple[int, int],
        move_func=None
    ) -> float:
        """
        Smooth mouse movement
        
        Args:
            start: Start point coordinates
            end: End point coordinates
            move_func: Movement function that accepts (x, y) parameters
            
        Returns:
            Movement duration
        """
        import pyautogui
        
        if move_func is None:
            move_func = pyautogui.moveTo
        
        # Generate curve path
        path = self.generate_bezier_curve(start, end)
        
        # Calculate movement time
        duration = random.uniform(self.config.move_duration_min, self.config.move_duration_max)
        step_delay = duration / len(path)
        
        start_time = time.time()
        
        # Execute movement
        for point in path:
            move_func(point[0], point[1])
            time.sleep(step_delay)
        
        elapsed = time.time() - start_time
        
        self.stats['total_moves'] += 1
        logger.debug(f"Smooth movement: {start} -> {end}, duration: {elapsed:.3f}s, points: {len(path)}")
        
        return elapsed
    
    def humanized_click(
        self, 
        x: int, 
        y: int, 
        button: str = 'left',
        click_func=None
    ):
        """
        Humanized click
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button
            click_func: Click function
        """
        import pyautogui
        
        if click_func is None:
            click_func = pyautogui.click
        
        # Add offset
        offset_x, offset_y = self.get_click_offset(x, y)
        
        # Random delay
        self.random_delay(0.05)
        
        # Execute click
        click_func(offset_x, offset_y, button=button)
        
        # Update statistics
        self.stats['total_clicks'] += 1
        current_time = time.time()
        
        if self.config.track_statistics:
            self.click_times.append(current_time)
            # Only keep data from the last 60 seconds
            self.click_times = [t for t in self.click_times if current_time - t < 60]
            self.stats['avg_click_frequency'] = len(self.click_times) / 60
        
        self.stats['last_click_time'] = current_time
        
        logger.debug(f"Humanized click: ({offset_x}, {offset_y}), button: {button}")
    
    def should_take_break(self, max_frequency: float = 5.0) -> bool:
        """
        Determine if a break is needed (prevent long-term high-frequency operations)
        
        Args:
            max_frequency: Maximum allowed frequency (times/second)"
            
        Returns:
            Whether a break is needed
        """
        if not self.config.track_statistics:
            return False
        
        current_freq = self.stats['avg_click_frequency']
        should_break = current_freq > max_frequency
        
        if should_break:
            logger.warning(f"Operation frequency too high ({current_freq:.2f}/s), recommended to take a break")
        
        return should_break
    
    def get_statistics(self) -> dict:
        """Get operation statistics"""
        return self.stats.copy()
    
    def reset_statistics(self):
        """Reset statistics data"""
        self.stats = {
            'total_clicks': 0,
            'total_moves': 0,
            'total_delays': 0,
            'avg_click_frequency': 0,
            'last_click_time': 0
        }
        self.click_times = []