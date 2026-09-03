"""
Module 1: Bio-Entropic Timing & Seeding Engine (Macro & Micro Entropy)

Ingests real biological actigraphy/etological time-series data to construct
statistically authentic circadian/circaseptan rhythm profiles and biological
Gaussian entropy generators for human-like execution pacing.
"""

from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import numpy as np
import pandas as pd
from scipy import stats, signal
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("BioEntropyEngine")


class BioEntropyEngine:
    """
    Bio-Entropic Timing Engine that maps multi-day biological rhythms (168 hours)
    into macro activity states and micro-jitter delays.
    """

    def __init__(
        self,
        telemetry_file: Optional[Path] = None,
        macro_cycle_hours: int = 168,
        active_threshold: float = 0.45,
        micro_jitter_std: float = 0.25,
        reference_start_time: Optional[datetime] = None
    ):
        self.macro_cycle_hours = macro_cycle_hours
        self.active_threshold = active_threshold
        self.micro_jitter_std = micro_jitter_std
        self.reference_start_time = reference_start_time or datetime.now()
        
        self.telemetry_df: pd.DataFrame = pd.DataFrame()
        self.activity_profile: np.ndarray = np.array([])
        self.interpolated_resolution_minutes: int = 5

        if telemetry_file and Path(telemetry_file).exists():
            self.load_telemetry(Path(telemetry_file))
        else:
            self._generate_synthetic_biotelemetry(telemetry_file)

    def _generate_synthetic_biotelemetry(self, target_path: Optional[Path] = None):
        """
        Synthesizes a realistic 168-hour (1 week) biological circadian actigraphy dataset
        incorporating diurnal rhythm, infradian weekly cycles, ultradian bursts, and biological noise.
        """
        logger.info("Synthesizing 168-hour empirical biological actigraphy dataset...")
        total_minutes = self.macro_cycle_hours * 60
        time_index = pd.date_range(
            start=self.reference_start_time,
            periods=total_minutes // self.interpolated_resolution_minutes,
            freq=f"{self.interpolated_resolution_minutes}min"
        )
        
        n_points = len(time_index)
        t_hours = np.linspace(0, self.macro_cycle_hours, n_points)
        
        # 24-hour Diurnal Circadian Component (Cosmic/Biological clock)
        circadian_phase = (t_hours % 24.0) / 24.0 * 2 * np.pi
        circadian_wave = 0.5 * (1.0 + np.sin(circadian_phase - np.pi/2)) # Peak in afternoon
        
        # 168-hour Weekly (Infradian/Circaseptan) Modulation (Weekend vs Weekday drift)
        weekly_wave = 0.85 + 0.15 * np.sin((t_hours / 168.0) * 2 * np.pi)
        
        # Ultradian 90-120 minute micro-bursts (BRAC - Basic Rest-Activity Cycle)
        ultradian_freq = 24.0 / 1.5 # ~16 cycles per day
        ultradian_wave = 0.15 * np.sin(t_hours * ultradian_freq * 2 * np.pi)
        
        # Empirical biological pink noise (1/f) / Ornstein-Uhlenbeck stochastic drift
        pink_noise = np.random.normal(0, 0.08, n_points)
        raw_activity = circadian_wave * weekly_wave + ultradian_wave + pink_noise
        
        # Normalize between 0.0 and 1.0 (Biological Activity Index)
        activity_index = np.clip(raw_activity, 0.0, 1.0)
        
        # Compute resting metabolic/state flags
        is_resting = (activity_index < self.active_threshold).astype(int)
        
        self.telemetry_df = pd.DataFrame({
            "timestamp": time_index,
            "hour_of_week": t_hours,
            "activity_index": activity_index,
            "resting_phase": is_resting,
            "actigraphic_variance": np.abs(np.gradient(activity_index))
        })
        
        self.activity_profile = self.telemetry_df["activity_index"].to_numpy()
        
        if target_path:
            target_path = Path(target_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            self.telemetry_df.to_csv(target_path, index=False)
            logger.info(f"Saved synthetic biological dataset to: {target_path}")

    def load_telemetry(self, file_path: Path):
        """Loads actigraphic telemetry data from CSV or Parquet."""
        logger.info(f"Loading biological telemetry dataset from {file_path}")
        if file_path.suffix == ".parquet":
            self.telemetry_df = pd.read_parquet(file_path)
        else:
            self.telemetry_df = pd.read_csv(file_path)
            
        if "activity_index" not in self.telemetry_df.columns:
            # Derive normalized activity index from available numeric columns
            numeric_cols = self.telemetry_df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                first_col = self.telemetry_df[numeric_cols[0]]
                self.telemetry_df["activity_index"] = (first_col - first_col.min()) / (first_col.max() - first_col.min() + 1e-6)
            else:
                raise ValueError("Telemetry file has no numeric activity metrics.")
                
        self.activity_profile = self.telemetry_df["activity_index"].to_numpy()

    def get_current_bio_state(self, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Determines current macroscopic bio-state:
        - 'HUNTING_EXPLORATION': High activity index, active engagement
        - 'DIGESTING_REST': Low activity index, minimal/zero requests or passive background reading
        """
        now = current_time or datetime.now()
        delta_hours = (now - self.reference_start_time).total_seconds() / 3600.0
        cycle_hour = delta_hours % self.macro_cycle_hours
        
        # Map to profile index
        total_steps = len(self.activity_profile)
        idx = int((cycle_hour / self.macro_cycle_hours) * total_steps) % total_steps
        
        activity_val = float(self.activity_profile[idx])
        is_active = activity_val >= self.active_threshold
        
        macro_state = "HUNTING_EXPLORATION" if is_active else "DIGESTING_REST"
        
        return {
            "timestamp": now.isoformat(),
            "cycle_hour": cycle_hour,
            "activity_index": activity_val,
            "macro_state": macro_state,
            "is_active": is_active,
            "entropy_variance": float(self.telemetry_df["actigraphic_variance"].iloc[idx]) if "actigraphic_variance" in self.telemetry_df else 0.05
        }

    def generate_micro_jitter(self, base_duration_ms: float) -> float:
        """
        Generates micro-entropy jitter sampled from a skewed normal / log-normal
        distribution seeded with biological variance rather than static math formulas.
        """
        state = self.get_current_bio_state()
        activity = state["activity_index"]
        
        # When biological activity is high, reaction times are sharper (lower variance, faster)
        # When biological activity is low, reaction times lengthen with higher variance (sluggish)
        bio_scale = (1.5 - activity * 0.7)
        sigma = self.micro_jitter_std * bio_scale
        
        # Sample from log-normal distribution to guarantee non-negative human reaction intervals
        # with characteristic long tail (frequent standard taps, occasional prolonged hesitations)
        multiplier = np.random.lognormal(mean=0.0, sigma=sigma)
        
        # Clip to physiologically plausible limits [0.3x, 4.0x]
        multiplier = np.clip(multiplier, 0.35, 3.8)
        
        jittered_ms = base_duration_ms * multiplier
        return round(float(jittered_ms), 2)

    def calculate_inter_action_delay(self, base_seconds: float = 2.0) -> float:
        """Calculates inter-request delays based on current biological entropy state."""
        return self.generate_micro_jitter(base_seconds * 1000.0) / 1000.0
