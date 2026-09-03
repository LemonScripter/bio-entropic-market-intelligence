"""
Orchestrator for the Bio-Entropic Web Data Collection & Market Analysis Framework.

Coordinates:
- Bio-Entropic Timing & Telemetry Engine
- Stochastic State Machine
- Stealth Browser Execution Layer
- Data Persistence & Downstream Export
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional
import random

from src.config import AppConfig
from src.bio_engine import BioEntropyEngine
from src.behavioral_motor import BehavioralStateMachine
from src.stealth_layer import StealthBrowserManager
from src.data_pipeline import MarketDataPipeline

# Configure unified logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
)
logger = logging.getLogger("BioEntropicOrchestrator")


class BioEntropicOrchestrator:
    """
    Main execution pipeline unifying biological entropy cycles with stealth web harvesting.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or AppConfig.load_default()
        self.bio_engine = BioEntropyEngine(
            telemetry_file=self.config.bio.telemetry_csv_path,
            macro_cycle_hours=self.config.bio.macro_cycle_hours,
            active_threshold=self.config.bio.active_threshold,
            micro_jitter_std=self.config.bio.micro_jitter_std
        )
        self.fsm = BehavioralStateMachine(name="AmazonMarketObserver")
        self.browser_manager = StealthBrowserManager(self.config, self.bio_engine)
        self.pipeline = MarketDataPipeline(self.config.storage.db_path)

    async def run_market_observation_session(self, target_keywords: List[str], max_pages_per_kw: int = 1):
        """
        Executes an end-to-end biological browsing and data collection cycle.
        """
        logger.info("Initializing Bio-Entropic Market Analysis Cycle...")
        
        # 1. Evaluate Current Biological Telemetry Phase
        bio_state = self.bio_engine.get_current_bio_state()
        logger.info(
            f"Bio-Macro State: {bio_state['macro_state']} | "
            f"Activity Index: {bio_state['activity_index']:.3f} | "
            f"Entropy Variance: {bio_state['entropy_variance']:.4f}"
        )

        if not bio_state["is_active"]:
            logger.info("Current cycle matches 'DIGESTING_REST' phase. Throttling execution to resting pace.")
            rest_delay = self.bio_engine.generate_micro_jitter(5000.0) / 1000.0
            await asyncio.sleep(rest_delay)

        # 2. Launch Stealth Browser Context
        context = await self.browser_manager.initialize()
        page = await context.new_page()

        try:
            self.fsm.start_exploration()

            for kw in target_keywords:
                logger.info(f"Preparing targeted market sweep for query: '{kw}'")
                self.fsm.initiate_search()

                # Navigate with organic timing
                await page.goto("https://www.amazon.com", wait_until="domcontentloaded", timeout=45000)
                
                # Inter-page cognitive dwell
                dwell_sec = self.bio_engine.calculate_inter_action_delay(base_seconds=2.5)
                await asyncio.sleep(dwell_sec)

                # Locate Search Box (Fallback to DOM if template matching is not supplied with reference PNG)
                search_box = await page.query_selector("input#twotabsearchtextbox")
                if search_box:
                    box_rect = await search_box.bounding_box()
                    if box_rect:
                        # Target middle of search box with subtle random offset
                        target_x = box_rect["x"] + box_rect["width"] / 2 + random.uniform(-10, 10)
                        target_y = box_rect["y"] + box_rect["height"] / 2 + random.uniform(-4, 4)
                        
                        await self.browser_manager.human_click(page, target_x, target_y)
                        await self.browser_manager.human_type(page, kw)
                        
                        # Press Enter with biological hesitation
                        enter_delay = self.bio_engine.generate_micro_jitter(180.0) / 1000.0
                        await asyncio.sleep(enter_delay)
                        await page.keyboard.press("Enter")
                        
                        # Wait for results to load
                        await page.wait_for_load_state("domcontentloaded")
                        self.fsm.consume_content()

                        # Natural viewport exploration / scroll
                        await self.browser_manager.human_scroll(page, scroll_distance_y=random.randint(600, 1200))
                        
                        read_dwell = self.bio_engine.calculate_inter_action_delay(base_seconds=3.5)
                        await asyncio.sleep(read_dwell)

                        # Extract SERP Content
                        html_content = await page.content()
                        products = self.pipeline.parse_product_card_html(html_content, category=kw)
                        if products:
                            self.pipeline.ingest_batch(products)
                            logger.info(f"Successfully recorded {len(products)} products into SQLite pipeline.")

                # Stochastic Resting injection between queries
                if random.random() < 0.4:
                    self.fsm.inject_pause()
                    pause_sec = self.bio_engine.calculate_inter_action_delay(base_seconds=4.0)
                    logger.info(f"Injecting stochastic distraction pause ({pause_sec:.2f}s)...")
                    await asyncio.sleep(pause_sec)
                    self.fsm.resume_activity()

            # 3. Export Analytics Downstream
            exports = self.pipeline.export_analytics(self.config.storage.export_csv_dir)
            logger.info(f"Cycle completed. Analytics exports available at:\n- {exports['csv']}\n- {exports['json']}")

        except Exception as e:
            logger.error(f"Encountered exception during orchestrator run: {e}", exc_info=True)
            self.fsm.inject_pause()
        finally:
            self.fsm.conclude_session()
            await self.browser_manager.close()


if __name__ == "__main__":
    orchestrator = BioEntropicOrchestrator()
    # Example execution run
    asyncio.run(orchestrator.run_market_observation_session(["mechanical keyboard wireless", "ergonomic mouse"]))
