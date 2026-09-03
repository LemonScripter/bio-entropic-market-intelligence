"""
Empirical Proof of Arbitrary-Volume Review Harvesting.
Extracts deep review pagination for 2 selected books (Atomic Habits & The Nightingale)
to demonstrably prove that any number of reviews can be harvested without restriction.
"""

import sys
import asyncio
import logging
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

from src.config import AppConfig
from src.bio_engine import BioEntropyEngine
from src.behavioral_motor import BehavioralStateMachine
from src.stealth_layer import StealthBrowserManager
from src.data_pipeline import MarketDataPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s"
)
logger = logging.getLogger("ProofHarvester")

DB_PATH = Path("data/market_data.db")
TARGET_BOOKS = [
    {"asin": "B07RFSSYBH", "title": "Atomic Habits", "author": "James Clear", "target_batches": 15},
    {"asin": "B00NY8OTR0", "title": "The Nightingale", "author": "Kristin Hannah", "target_batches": 15}
]

async def run_proof():
    config = AppConfig.load_default()
    config.browser.headless = True
    
    bio_engine = BioEntropyEngine(
        telemetry_file=config.bio.telemetry_file,
        macro_cycle_hours=config.bio.macro_cycle_hours,
        active_threshold=config.bio.active_threshold
    )
    fsm = BehavioralStateMachine(bio_engine)
    stealth = StealthBrowserManager(config, bio_engine)
    pipeline = MarketDataPipeline(DB_PATH)
    
    context = await stealth.initialize()
    page = await context.new_page()
    
    proof_results = {}
    
    for book_info in TARGET_BOOKS:
        asin = book_info["asin"]
        title = book_info["title"]
        author = book_info["author"]
        target_batches = book_info["target_batches"]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"PROVING DEEP HARVEST FOR: {title} by {author} (ASIN: {asin})")
        logger.info(f"Targeting {target_batches} pagination batches (~150+ reviews)...")
        logger.info(f"{'='*60}")
        
        url = f"https://www.amazon.com/product-reviews/{asin}"
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(2)
        
        collected_reviews = {}
        batch_progression = []
        
        for batch_num in range(1, target_batches + 1):
            await stealth.human_scroll(page, scroll_distance_y=2000)
            await asyncio.sleep(1.0)
            
            html = await page.content()
            dom_reviews = pipeline.parse_product_reviews_html(html, asin)
            
            new_in_batch = 0
            for r in dom_reviews:
                if r["review_id"] not in collected_reviews:
                    collected_reviews[r["review_id"]] = r
                    new_in_batch += 1
            
            batch_progression.append({
                "batch": batch_num,
                "visible_on_dom": len(dom_reviews),
                "cumulative_unique": len(collected_reviews),
                "new_added": new_in_batch
            })
            
            logger.info(f"  [Batch {batch_num:02d}/{target_batches:02d}] "
                        f"Cumulative Unique Reviews: {len(collected_reviews)} (+{new_in_batch} newly loaded)")
            
            # Click more button
            btn_selector = '#cm_cr-pagination_bar a, a:has-text("Show 10 more reviews"), a:has-text("Next page"), li.a-last a'
            try:
                more_btn = await page.query_selector(btn_selector)
                if more_btn and await more_btn.is_visible():
                    await more_btn.click()
                    await asyncio.sleep(2.0)
                else:
                    logger.info("  -> Reached end of review stream.")
                    break
            except Exception as e:
                logger.warning(f"  -> Click note: {e}")
                break
        
        # Save batch into SQLite
        pipeline.ingest_reviews_batch(list(collected_reviews.values()))
        
        proof_results[asin] = {
            "title": title,
            "author": author,
            "total_extracted": len(collected_reviews),
            "batches": batch_progression,
            "reviews": list(collected_reviews.values())
        }
        
        # Short human delay between books
        delay = bio_engine.generate_micro_jitter(2000.0) / 1000.0
        await asyncio.sleep(delay)

    await stealth.close()
    
    # Generate Proof CSV and Summary
    all_proof_reviews = []
    for asin, data in proof_results.items():
        all_proof_reviews.extend(data["reviews"])
        
    df_proof = pd.DataFrame(all_proof_reviews)
    export_file = Path("data/exports/empirical_proof_2_books.csv")
    export_file.parent.mkdir(parents=True, exist_ok=True)
    df_proof.to_csv(export_file, index=False, encoding="utf-8")
    
    logger.info(f"\n{'='*60}")
    logger.info("PROOF HARVESTING COMPLETE!")
    logger.info(f"Exported {len(all_proof_reviews)} reviews to: {export_file}")
    for asin, data in proof_results.items():
        logger.info(f"  - {data['title']} ({data['author']}): {data['total_extracted']} reviews across {len(data['batches'])} batches.")
    logger.info(f"{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(run_proof())
