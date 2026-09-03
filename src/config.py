"""
Configuration definitions for the Bio-Entropic Framework.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

@dataclass
class ProxyConfig:
    enabled: bool = False
    server: str = "http://residential.proxy-provider.com:8000"
    username: Optional[str] = None
    password: Optional[str] = None
    rotation_on_rest: bool = True
    utls_enabled: bool = False
    utls_client_hello: str = "chrome_120"

@dataclass
class BrowserConfig:
    headless: bool = False
    user_data_dir: Path = BASE_DIR / "data" / "user_data"
    storage_state_path: Path = BASE_DIR / "data" / "sessions" / "session_state.json"
    viewport_width: int = 1920
    viewport_height: int = 1080
    locale: str = "en-US"
    timezone_id: str = "America/New_York"
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

@dataclass
class BioEntropyConfig:
    telemetry_csv_path: Path = BASE_DIR / "data" / "telemetry" / "actigraphy_168h.csv"
    macro_cycle_hours: int = 168  # 1 week circadian/circaseptan rhythm
    active_phase_threshold: float = 0.45  # Activity index above which macro state is Active
    micro_jitter_std: float = 0.25  # Relative standard deviation for Gaussian noise
    base_typing_delay_ms: float = 85.0
    base_click_dwell_ms: float = 140.0

    @property
    def active_threshold(self) -> float:
        return self.active_phase_threshold

    @property
    def telemetry_file(self) -> Path:
        return self.telemetry_csv_path

    @telemetry_file.setter
    def telemetry_file(self, val: Any):
        self.telemetry_csv_path = Path(val) if val else None

@dataclass
class StorageConfig:
    db_path: Path = BASE_DIR / "data" / "market_data.db"
    export_json_dir: Path = BASE_DIR / "data" / "exports"
    export_csv_dir: Path = BASE_DIR / "data" / "exports"

    @property
    def export_dir(self) -> Path:
        return self.export_csv_dir

@dataclass
class AppConfig:
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    bio: BioEntropyConfig = field(default_factory=BioEntropyConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)

    @classmethod
    def load_default(cls) -> "AppConfig":
        config = cls()
        # Ensure requisite local directories exist
        config.browser.user_data_dir.mkdir(parents=True, exist_ok=True)
        config.browser.storage_state_path.parent.mkdir(parents=True, exist_ok=True)
        config.bio.telemetry_csv_path.parent.mkdir(parents=True, exist_ok=True)
        config.storage.db_path.parent.mkdir(parents=True, exist_ok=True)
        config.storage.export_json_dir.mkdir(parents=True, exist_ok=True)
        return config
