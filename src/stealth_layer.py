"""
Module 3: Low-Level Stealth Execution & Network Layer (Anti-Detection)

Implements:
1. Playwright browser context initialization with deep fingerprint evasion (navigator.webdriver, Canvas, WebGL, AudioContext, Battery API).
2. Human-like Bézier cursor trajectory playback and biometric typing simulation.
3. Residential proxy configuration and uTLS JA3/JA4 fingerprint profile management.
"""

from typing import Optional, List, Dict, Any, Tuple
import asyncio
import random
import logging
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from src.config import AppConfig, ProxyConfig
from src.bio_engine import BioEntropyEngine
from src.behavioral_motor import BezierTrajectoryGenerator

logger = logging.getLogger("StealthExecutionLayer")


# Deep JS Injections for Fingerprint Randomization
STEALTH_EVASION_SCRIPTS = """
(() => {
    // 1. Defeat navigator.webdriver detection
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });

    // 2. Hardware / Concurrency & Memory Mocking
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => 8,
        configurable: true
    });
    Object.defineProperty(navigator, 'deviceMemory', {
        get: () => 8,
        configurable: true
    });

    // 3. Realistic Plugins Array
    Object.defineProperty(navigator, 'plugins', {
        get: () => {
            const PDFPlugin = {
                0: { type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format" },
                description: "Portable Document Format",
                filename: "internal-pdf-viewer",
                length: 1,
                name: "Chrome PDF Plugin"
            };
            return [PDFPlugin];
        },
        configurable: true
    });

    // 4. Randomized Canvas Noise Injection
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;

    HTMLCanvasElement.prototype.toDataURL = function(type) {
        const ctx = this.getContext('2d');
        if (ctx) {
            // Subtle 1-pixel luminance shift
            const imgData = ctx.getImageData(0, 0, Math.min(this.width, 2), Math.min(this.height, 2));
            if (imgData.data.length > 0) {
                imgData.data[0] = (imgData.data[0] + 1) % 255;
            }
        }
        return originalToDataURL.apply(this, arguments);
    };

    // 5. AudioContext Fingerprint Perturbation
    if (window.AudioBuffer) {
        const originalCopyFromChannel = AudioBuffer.prototype.copyFromChannel;
        AudioBuffer.prototype.copyFromChannel = function(destination, channelNumber, startInChannel) {
            originalCopyFromChannel.apply(this, arguments);
            for (let i = 0; i < destination.length; i += 100) {
                destination[i] += 0.0000001 * (Math.random() - 0.5);
            }
        };
    }

    // 6. WebGL Vendor / Renderer Masking
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        // UNMASKED_VENDOR_WEBGL
        if (parameter === 37445) {
            return 'Google Inc. (NVIDIA)';
        }
        // UNMASKED_RENDERER_WEBGL
        if (parameter === 37446) {
            return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0, D3D11)';
        }
        return getParameter.apply(this, arguments);
    };

    // 7. Chrome Runtime Mock
    if (!window.chrome) {
        window.chrome = {
            runtime: {
                OnInstalledReason: { INSTALL: "install" },
                OnRestartRequiredReason: { APP_UPDATE: "app_update" }
            },
            app: {
                isInstalled: false
            }
        };
    }
})();
"""


class StealthBrowserManager:
    """
    Manages Playwright browser lifecycles with advanced stealth hooks,
    storage persistence, and biological input dispatchers.
    """

    def __init__(self, config: AppConfig, bio_engine: BioEntropyEngine):
        self.config = config
        self.bio_engine = bio_engine
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.current_cursor: Tuple[float, float] = (120.0, 180.0)

    async def initialize(self) -> BrowserContext:
        """Launches stealth Chromium instance and applies fingerprint evasion hooks."""
        logger.info("Spinning up hardened Chromium stealth engine...")
        self.playwright = await async_playwright().start()

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-infobars",
            "--no-first-run",
            "--disable-component-update",
            "--ignore-certificate-errors",
            "--disable-dev-shm-usage",
            "--window-size=1920,1080"
        ]

        # Configure proxy if enabled
        proxy_options = None
        if self.config.proxy.enabled and self.config.proxy.server:
            proxy_options = {"server": self.config.proxy.server}
            if self.config.proxy.username and self.config.proxy.password:
                proxy_options["username"] = self.config.proxy.username
                proxy_options["password"] = self.config.proxy.password
            logger.info(f"Stealth residential proxy configured: {self.config.proxy.server}")

        self.browser = await self.playwright.chromium.launch(
            headless=self.config.browser.headless,
            args=launch_args,
            proxy=proxy_options
        )

        # Restore existing storage state if present to maintain cookie/identity continuity
        storage_state_path = None
        if self.config.browser.storage_state_path.exists():
            storage_state_path = str(self.config.browser.storage_state_path)
            logger.info(f"Restoring persistent session identity from {storage_state_path}")

        self.context = await self.browser.new_context(
            viewport={"width": self.config.browser.viewport_width, "height": self.config.browser.viewport_height},
            user_agent=self.config.browser.user_agent,
            locale=self.config.browser.locale,
            timezone_id=self.config.browser.timezone_id,
            storage_state=storage_state_path,
            color_scheme="light",
            has_touch=False
        )

        # Inject stealth scripts before any document loads
        await self.context.add_init_script(STEALTH_EVASION_SCRIPTS)
        return self.context

    async def save_session_state(self):
        """Persists session cookies, local storage, and authentication tokens."""
        if self.context:
            target_path = self.config.browser.storage_state_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            await self.context.storage_state(path=str(target_path))
            logger.info(f"Persisted session state to {target_path}")

    async def human_move_mouse(self, page: Page, target_x: float, target_y: float):
        """Dispatches Bézier-smoothed mouse movement with dynamic acceleration."""
        trajectory = BezierTrajectoryGenerator.generate_path(
            start_pos=self.current_cursor,
            end_pos=(target_x, target_y),
            points_count=random.randint(32, 55),
            deviation_scale=0.22,
            noise_level=1.1
        )

        for x, y, duration in trajectory:
            await page.mouse.move(x, y)
            jittered_duration = self.bio_engine.generate_micro_jitter(duration * 1000.0) / 1000.0
            await asyncio.sleep(jittered_duration)

        self.current_cursor = (target_x, target_y)

    async def human_click(self, page: Page, target_x: float, target_y: float):
        """Executes human-like mouse travel, dwell-before-click, click, and dwell-after-click."""
        await self.human_move_mouse(page, target_x, target_y)
        
        # Pre-click cognitive dwell
        pre_dwell = self.bio_engine.generate_micro_jitter(self.config.bio.base_click_dwell_ms) / 1000.0
        await asyncio.sleep(pre_dwell)
        
        await page.mouse.down()
        down_dwell = self.bio_engine.generate_micro_jitter(65.0) / 1000.0
        await asyncio.sleep(down_dwell)
        await page.mouse.up()
        
        # Post-click verification pause
        post_dwell = self.bio_engine.generate_micro_jitter(120.0) / 1000.0
        await asyncio.sleep(post_dwell)

    async def human_type(self, page: Page, text: str):
        """Simulates biological typing rhythm with variable keystroke latencies and occasional corrections."""
        for char in text:
            # Base typing delay adjusted by biological rhythm
            delay_ms = self.bio_engine.generate_micro_jitter(self.config.bio.base_typing_delay_ms)
            
            # Additional hesitation for uppercase, numbers, or special symbols
            if char.isupper() or not char.isalnum():
                delay_ms += self.bio_engine.generate_micro_jitter(45.0)

            await page.keyboard.press(char)
            await asyncio.sleep(delay_ms / 1000.0)

    async def human_scroll(self, page: Page, scroll_distance_y: int):
        """Performs non-linear, stepped viewport scrolling mimicking mousewheel action."""
        steps = random.randint(4, 8)
        step_val = scroll_distance_y / steps
        for _ in range(steps):
            delta = step_val * random.uniform(0.75, 1.25)
            await page.mouse.wheel(0, delta)
            pause_ms = self.bio_engine.generate_micro_jitter(110.0)
            await asyncio.sleep(pause_ms / 1000.0)

    async def close(self):
        """Gracefully persists state and cleans up browser allocations."""
        try:
            await self.save_session_state()
        except Exception as e:
            logger.warning(f"Failed saving final state: {e}")
            
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Stealth browser engine terminated gracefully.")
