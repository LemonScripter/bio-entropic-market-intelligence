"""
Module 2: Stochastic State-Machine & Behavioral Motor (State & Movement)

Implements:
1. Finite State Machine (FSM) utilizing `transitions` for macro and micro state navigation.
2. Mathematically pure Bézier curve trajectory generation with dynamic velocity profiles.
3. OpenCV Computer Vision Template Matching for dynamic element discovery and visual interaction.
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import cv2
from transitions import Machine
import logging
import time
import math
import io
from PIL import Image

logger = logging.getLogger("BehavioralMotor")


class BezierTrajectoryGenerator:
    """
    Generates human-like cursor trajectories using cubic and higher-order
    Bézier curves with physiological acceleration/deceleration profiles (Fitts's Law).
    """

    @staticmethod
    def _binomial(n: int, k: int) -> float:
        """Computes binomial coefficient (n choose k)."""
        return math.comb(n, k)

    @staticmethod
    def _bezier_point(control_points: np.ndarray, t: float) -> np.ndarray:
        """Calculates a single point along a Bézier curve for parameter t in [0, 1]."""
        n = len(control_points) - 1
        point = np.zeros(2, dtype=np.float64)
        for i, p in enumerate(control_points):
            b = BezierTrajectoryGenerator._binomial(n, i) * ((1 - t) ** (n - i)) * (t ** i)
            point += b * p
        return point

    @classmethod
    def generate_path(
        cls,
        start_pos: Tuple[float, float],
        end_pos: Tuple[float, float],
        points_count: int = 40,
        deviation_scale: float = 0.25,
        noise_level: float = 1.2
    ) -> List[Tuple[float, float, float]]:
        """
        Generates a full (x, y, duration_step) trajectory from start_pos to end_pos.
        Includes 2 randomized control points mimicking human neuromuscular curvature
        and non-linear velocity distribution (ease-in-out ease-deceleration).
        """
        p0 = np.array(start_pos, dtype=np.float64)
        p3 = np.array(end_pos, dtype=np.float64)
        
        distance = np.linalg.norm(p3 - p0)
        if distance < 5.0:
            return [(end_pos[0], end_pos[1], 0.05)]
            
        # Perpendicular vector for natural arc drift
        delta = p3 - p0
        perp = np.array([-delta[1], delta[0]])
        perp_len = np.linalg.norm(perp)
        if perp_len > 0:
            perp = perp / perp_len
        else:
            perp = np.array([0.0, 1.0])
            
        # Generate two randomized internal control points P1 and P2
        drift_1 = np.random.uniform(-deviation_scale, deviation_scale) * distance
        drift_2 = np.random.uniform(-deviation_scale * 0.7, deviation_scale * 0.7) * distance
        
        p1 = p0 + delta * np.random.uniform(0.2, 0.4) + perp * drift_1
        p2 = p0 + delta * np.random.uniform(0.6, 0.8) + perp * drift_2
        
        control_points = np.array([p0, p1, p2, p3])
        
        # Velocity profile according to Fitts's Law / Minimum-Jerk Model
        # Using a parameterized Beta distribution for human-like acceleration curve
        raw_t = np.linspace(0.0, 1.0, points_count)
        # S-curve ease-in-out mapping:
        t_mapped = 0.5 * (1 - np.cos(np.pi * raw_t))
        
        trajectory = []
        for idx, t in enumerate(t_mapped):
            pt = cls._bezier_point(control_points, t)
            # Add subtle hand tremor / micro-jitter (white noise filtered)
            if 0 < idx < points_count - 1:
                pt += np.random.normal(0, noise_level, 2)
                
            # Inter-point time step in seconds (faster in middle, slower at targets)
            step_duration = 0.008 + 0.015 * (1.0 - np.sin(np.pi * t))
            trajectory.append((float(pt[0]), float(pt[1]), float(step_duration)))
            
        return trajectory


class VisualElementDetector:
    """
    Computer Vision Engine using OpenCV Template Matching with multi-scale pyramid
    analysis to detect UI components irrespective of brittle DOM changes.
    """

    @staticmethod
    def match_template_on_image(
        screenshot_bytes: bytes,
        template_bytes: bytes,
        threshold: float = 0.82
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Locates template within screenshot using cv2.TM_CCOEFF_NORMED.
        Returns bounding box (center_x, center_y, width, height) or None.
        """
        try:
            # Decode images to numpy arrays
            scr_arr = np.frombuffer(screenshot_bytes, dtype=np.uint8)
            tpl_arr = np.frombuffer(template_bytes, dtype=np.uint8)
            
            screen_img = cv2.imdecode(scr_arr, cv2.IMREAD_COLOR)
            template_img = cv2.imdecode(tpl_arr, cv2.IMREAD_COLOR)
            
            if screen_img is None or template_img is None:
                logger.warning("Failed to decode screenshot or template image buffer.")
                return None
                
            # Convert to grayscale for robust luminance invariance
            screen_gray = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
            
            th, tw = template_gray.shape[:2]
            
            # Multi-scale template matching across 0.8x to 1.2x scale factors
            best_match = None
            best_val = -1.0
            
            for scale in np.linspace(0.85, 1.15, 7):
                resized_w = int(tw * scale)
                resized_h = int(th * scale)
                if resized_w > screen_gray.shape[1] or resized_h > screen_gray.shape[0]:
                    continue
                    
                resized_tpl = cv2.resize(template_gray, (resized_w, resized_h), interpolation=cv2.INTER_AREA)
                res = cv2.matchTemplate(screen_gray, resized_tpl, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                
                if max_val > best_val:
                    best_val = max_val
                    top_left = max_loc
                    best_match = (
                        top_left[0] + resized_w // 2,
                        top_left[1] + resized_h // 2,
                        resized_w,
                        resized_h
                    )
                    
            if best_val >= threshold and best_match:
                logger.info(f"Visual template match found with confidence {best_val:.3f} at center {best_match[:2]}")
                return best_match
            else:
                logger.debug(f"Template match below threshold ({best_val:.3f} < {threshold})")
                return None
                
        except Exception as e:
            logger.error(f"Error during OpenCV template matching: {e}")
            return None


class BehavioralStateMachine:
    """
    Finite State Machine managing organic browsing flows:
    - IDLE: Resting or waiting between cycles
    - EXPLORING: Broad category browsing, landing page discovery
    - SEARCHING: Focused query composition and input
    - READING: Organic dwell times, variable scroll rates
    - ENTROPY_REST: Injected idle timeouts (stepping away, distraction pauses)
    """

    states = [
        "idle",
        "exploring",
        "searching",
        "reading",
        "entropy_rest"
    ]

    transitions_def = [
        {"trigger": "start_exploration", "source": "idle", "dest": "exploring"},
        {"trigger": "initiate_search", "source": ["idle", "exploring", "reading"], "dest": "searching"},
        {"trigger": "consume_content", "source": ["searching", "exploring"], "dest": "reading"},
        {"trigger": "inject_pause", "source": "*", "dest": "entropy_rest"},
        {"trigger": "resume_activity", "source": "entropy_rest", "dest": "exploring"},
        {"trigger": "conclude_session", "source": "*", "dest": "idle"},
    ]

    def __init__(self, name: str = "MarketAnalyst"):
        self.name = name
        self.current_cursor_pos: Tuple[float, float] = (100.0, 100.0)
        self.machine = Machine(
            model=self,
            states=BehavioralStateMachine.states,
            transitions=BehavioralStateMachine.transitions_def,
            initial="idle",
            send_event=True
        )

    def on_enter_exploring(self, event=None):
        logger.info(f"[{self.name}] State transitioned to: EXPLORING (Broad browsing)")

    def on_enter_searching(self, event=None):
        logger.info(f"[{self.name}] State transitioned to: SEARCHING (Formulating keyword inquiry)")

    def on_enter_reading(self, event=None):
        logger.info(f"[{self.name}] State transitioned to: READING (Ingesting product DOM/content)")

    def on_enter_entropy_rest(self, event=None):
        logger.info(f"[{self.name}] State transitioned to: ENTROPY_REST (Bio-pause / distraction timeout)")

    def on_enter_idle(self, event=None):
        logger.info(f"[{self.name}] State transitioned to: IDLE (Session dormant)")
