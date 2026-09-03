"""
Dedicated Review Harvester for Top Books.
Visits individual product review pages using the Bio-Entropic Stealth Engine
and populates the SQLite 'reviews' and 'products' tables with granular customer data.
"""

import sys
import asyncio
import sqlite3
import random
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import AppConfig
from src.bio_engine import BioEntropyEngine
from src.stealth_layer import StealthBrowserManager
from src.data_pipeline import MarketDataPipeline
from src.behavioral_motor import BehavioralStateMachine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
)
logger = logging.getLogger("ReviewHarvester")


async def harvest_top_books_reviews(limit: int = 10):
    config = AppConfig.load_default()
    config.browser.headless = True

    bio_engine = BioEntropyEngine(
        telemetry_file=config.bio.telemetry_file,
        macro_cycle_hours=config.bio.macro_cycle_hours,
        active_threshold=config.bio.active_threshold,
        micro_jitter_std=config.bio.micro_jitter_std
    )
    browser_manager = StealthBrowserManager(config, bio_engine)
    pipeline = MarketDataPipeline(config.storage.db_path)
    fsm = BehavioralStateMachine(name="BookReviewHarvester")

    # Fetch top books from database
    with sqlite3.connect(config.storage.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT asin, title FROM products
            WHERE title NOT LIKE '%Keyboard%' AND title NOT LIKE '%Mouse%'
            ORDER BY rating DESC, ratings_count DESC
            LIMIT ?
        """, (limit,))
        target_books = cursor.fetchall()

    if not target_books:
        logger.warning("No books found in database to harvest.")
        return

    logger.info(f"Targeting {len(target_books)} bestseller books for deep review extraction.")

    context = await browser_manager.initialize()
    page = await context.new_page()

    try:
        fsm.start_exploration()

        for idx, (asin, title) in enumerate(target_books, 1):
            logger.info(f"[{idx}/{len(target_books)}] Harvesting reviews for ASIN: {asin} ('{title[:45]}...')")
            fsm.initiate_search()

            # Navigate to dedicated customer reviews page
            review_url = f"https://www.amazon.com/product-reviews/{asin}?sortBy=recent"
            
            try:
                await page.goto(review_url, wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                logger.warning(f"Timeout loading review page for {asin}: {e}")
                continue

            # Inter-page cognitive dwell
            dwell = bio_engine.calculate_inter_action_delay(base_seconds=2.0)
            await asyncio.sleep(dwell)

            # Scroll down to mimic organic reading
            fsm.consume_content()
            await browser_manager.human_scroll(page, scroll_distance_y=random.randint(500, 1000))
            
            read_pause = bio_engine.calculate_inter_action_delay(base_seconds=2.5)
            await asyncio.sleep(read_pause)

            # Extract HTML and parse reviews
            html_content = await page.content()
            reviews = pipeline.parse_product_reviews_html(html_content, asin)

            if not reviews:
                # Direct product page review fallback
                logger.info(f"Direct review page yielded 0, navigating to /dp/{asin} for '{title[:35]}'...")
                dp_url = f"https://www.amazon.com/dp/{asin}"
                await page.goto(dp_url, wait_until="domcontentloaded", timeout=40000)
                await browser_manager.human_scroll(page, scroll_distance_y=random.randint(900, 1600))
                await asyncio.sleep(2.0)
                dp_html = await page.content()
                reviews = pipeline.parse_product_reviews_html(dp_html, asin)

            if reviews:
                pipeline.ingest_reviews_batch(reviews)
                logger.info(f"-> [SUCCESS] Ingested {len(reviews)} customer reviews for '{title[:35]}'")
            else:
                logger.warning(f"-> [EMPTY] No customer reviews extracted for ASIN: {asin}")

            # Stochastic bio-pause between books
            fsm.inject_pause()
            pause = bio_engine.generate_micro_jitter(2200.0) / 1000.0
            await asyncio.sleep(pause)
            fsm.resume_activity()

        # Export updated analytics
        export_paths = pipeline.export_analytics(config.storage.export_dir)
        logger.info(f"Review harvesting finished. Export files:\n{export_paths}")

    finally:
        await browser_manager.close()


if __name__ == "__main__":
    asyncio.run(harvest_top_books_reviews(limit=10))

