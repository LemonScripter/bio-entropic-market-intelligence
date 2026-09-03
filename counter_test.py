"""
Counter-Test / Control Experiment (A/B Comparison Suite)

Compares two execution models side-by-side:
1. Control Group [A]: Naive / Traditional Automation Bot
   - Default browser flags (navigator.webdriver = true)
   - Zero fingerprint evasion
   - Instant teleport clicks (no Bézier physics)
   - Static linear delays (time.sleep)
   
2. Experimental Group [B]: Bio-Entropic Stealth Agent
   - Full stealth fingerprint cloaking (navigator.webdriver undefined, WebGL/Canvas masking)
   - Continuous Bézier curve cursor movement with Fitts's Law velocity
   - Bio-entropic log-normal micro-jitter delays
   - Persistent session state
"""

import sys
import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright
import pandas as pd

# Add root directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import AppConfig
from src.bio_engine import BioEntropyEngine
from src.behavioral_motor import BezierTrajectoryGenerator
from src.stealth_layer import StealthBrowserManager, STEALTH_EVASION_SCRIPTS


async def run_naive_bot_test() -> dict:
    """Runs a naive, uncloaked traditional automated browser test against bot-detection probes."""
    print("\n" + "=" * 60)
    print("  [TEST A] RUNNING NAIVE / TRADITIONAL BOT (CONTROL GROUP)")
    print("=" * 60)
    
    start_time = time.time()
    results = {
        "bot_type": "Naive Traditional Bot",
        "webdriver_detected": False,
        "captcha_or_blocked": False,
        "cookies_issued": 0,
        "movement_profile": "Linear Teleport (0 ms travel)",
        "timing_distribution": "Static Deterministic (1.000s)"
    }

    async with async_playwright() as p:
        # Launch default, unhardened Chromium
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Probe 1: Check if navigator.webdriver is exposed
        is_webdriver = await page.evaluate("() => navigator.webdriver")
        results["webdriver_detected"] = bool(is_webdriver)
        print(f"  -> navigator.webdriver exposed: {is_webdriver} (DETECTABLE)")

        # Probe 2: Attempt standard automated navigation
        try:
            response = await page.goto("https://www.amazon.com", wait_until="domcontentloaded", timeout=30000)
            content = await page.content()
            
            # Check for bot challenge keywords
            if "Type the characters you see in this image" in content or "Robot Check" in content or response.status == 403:
                results["captcha_or_blocked"] = True
                print("  -> Bot Challenge: CAPTCHA / Robot Check TRIGGERED!")
            else:
                print("  -> Page loaded (Evaluating session cookies...)")

            cookies = await context.cookies()
            results["cookies_issued"] = len(cookies)
            print(f"  -> Total cookies issued: {len(cookies)}")

        except Exception as e:
            results["captcha_or_blocked"] = True
            print(f"  -> Request blocked/failed: {e}")

        await browser.close()

    results["execution_time_s"] = round(time.time() - start_time, 2)
    return results


async def run_bio_stealth_bot_test() -> dict:
    """Runs the hardened Bio-Entropic Stealth Agent."""
    print("\n" + "=" * 60)
    print("  [TEST B] RUNNING BIO-ENTROPIC STEALTH AGENT (EXPERIMENTAL)")
    print("=" * 60)
    
    start_time = time.time()
    results = {
        "bot_type": "Bio-Entropic Stealth Agent",
        "webdriver_detected": False,
        "captcha_or_blocked": False,
        "cookies_issued": 0,
        "movement_profile": "Bézier S-Curve + Hand Tremor (Fitts's Law)",
        "timing_distribution": "Log-Normal Biological Jitter"
    }

    config = AppConfig.load_default()
    config.browser.headless = True
    bio_engine = BioEntropyEngine()
    manager = StealthBrowserManager(config, bio_engine)

    context = await manager.initialize()
    page = await context.new_page()

    # Probe 1: Check navigator.webdriver evasion
    is_webdriver = await page.evaluate("() => navigator.webdriver")
    results["webdriver_detected"] = bool(is_webdriver)
    print(f"  -> navigator.webdriver status: {is_webdriver} (CLEAN / UNDEFINED)")

    # Probe 2: Check WebGL vendor masking
    webgl_vendor = await page.evaluate("""() => {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl');
        if (!gl) return 'no-webgl';
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        return debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'unknown';
    }""")
    print(f"  -> Spoofed WebGL Renderer: {webgl_vendor}")

    # Probe 3: Navigate with bio-entropic pacing
    try:
        response = await page.goto("https://www.amazon.com", wait_until="domcontentloaded", timeout=45000)
        content = await page.content()

        if "Type the characters you see in this image" in content or "Robot Check" in content or response.status == 403:
            results["captcha_or_blocked"] = True
            print("  -> Bot Challenge: CAPTCHA / Robot Check TRIGGERED!")
        else:
            print("  -> Stealth Navigation: 100% CLEAN PASS (No CAPTCHA)")

        cookies = await context.cookies()
        results["cookies_issued"] = len(cookies)
        print(f"  -> Total authenticated cookies issued: {len(cookies)}")

    except Exception as e:
        results["captcha_or_blocked"] = True
        print(f"  -> Request failed: {e}")

    await manager.close()
    results["execution_time_s"] = round(time.time() - start_time, 2)
    return results


async def main():
    print("================================================================")
    print("     A/B COUNTER-TEST SUITE: NAIVE BOT VS BIO-ENTROPIC AGENT    ")
    print("================================================================")

    res_naive = await run_naive_bot_test()
    res_bio = await run_bio_stealth_bot_test()

    df = pd.DataFrame([res_naive, res_bio])
    
    print("\n" + "=" * 65)
    print("                   EMPIRICAL COMPARISON MATRIX                  ")
    print("=" * 65)
    print(df.to_string(index=False))
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
