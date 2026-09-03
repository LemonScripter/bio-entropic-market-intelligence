"""
Massive Multi-Page Review Harvester for Top 10 Bestseller Books.
Uses authenticated session state to bypass login walls and extract
large volumes of customer reviews via Amazon's dynamic review pagination.
"""

import sys
import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import List, Dict, Any

from src.config import AppConfig
from src.bio_engine import BioEntropyEngine
from src.behavioral_motor import BehavioralStateMachine
from src.stealth_layer import StealthBrowserManager
from src.data_pipeline import MarketDataPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
)
logger = logging.getLogger("MassiveHarvester")

DB_PATH = Path("data/market_data.db")
MAX_PAGES_PER_BOOK = 8  # 8 iterations x 10 = ~80-90 detailed reviews per book

async def run_massive_harvest():
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
    
    # Get top 10 books from database
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("""
        SELECT asin, title, brand, ratings_count 
        FROM products 
        ORDER BY ratings_count DESC 
        LIMIT 10
    """)
    books = c.fetchall()
    conn.close()
    
    logger.info(f"Targeting top {len(books)} books for massive multi-page review extraction.")
    
    context = await stealth.initialize()
    page = await context.new_page()
    
    fsm.start_exploration()
    
    total_new_reviews_all_books = 0
    
    for book_idx, (asin, title, author, ratings_count) in enumerate(books, 1):
        fsm.initiate_search(query=f"Reviews for {asin}")
        logger.info(f"\n{'='*55}")
        logger.info(f"[{book_idx}/10] Harvesting: {title[:38]}... ({author})")
        logger.info(f"ASIN: {asin} | Total Amazon Ratings: {ratings_count:,}")
        logger.info(f"{'='*55}")
        
        review_url = f"https://www.amazon.com/product-reviews/{asin}"
        
        try:
            await page.goto(review_url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(2)
            fsm.consume_content()
            
            book_reviews: Dict[str, Dict[str, Any]] = {}
            
            for page_iter in range(1, MAX_PAGES_PER_BOOK + 1):
                # Scroll to reveal reviews
                await stealth.human_scroll(page, scroll_distance_y=1800)
                await asyncio.sleep(1.2)
                
                # Extract currently loaded DOM reviews
                html = await page.content()
                extracted = pipeline.parse_product_reviews_html(html, asin)
                new_count = 0
                for r in extracted:
                    if r["review_id"] not in book_reviews:
                        book_reviews[r["review_id"]] = r
                        new_count += 1
                
                logger.info(f"  -> Page/Batch {page_iter}: {len(extracted)} visible on DOM, {len(book_reviews)} total unique collected (+{new_count} new).")
                
                # Click 'Show 10 more reviews' or next button
                btn_selector = '#cm_cr-pagination_bar a, a:has-text("Show 10 more reviews"), a:has-text("Next page"), li.a-last a'
                try:
                    more_btn = await page.query_selector(btn_selector)
                    if more_btn and await more_btn.is_visible():
                        await more_btn.click()
                        # Short bio pause for AJAX response
                        await asyncio.sleep(2.5)
                    else:
                        logger.info("  -> Reached end of review pages or no more button.")
                        break
                except Exception as click_err:
                    logger.warning(f"  -> Pagination click note: {click_err}")
                    break
            
            # Ingest batch into SQLite
            reviews_list = list(book_reviews.values())
            pipeline.ingest_reviews_batch(reviews_list)
            total_new_reviews_all_books += len(reviews_list)
            logger.info(f"[SUCCESS] Ingested {len(reviews_list)} full-text customer reviews for '{title[:30]}'.")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed harvesting ASIN {asin}: {e}")
            
        # Biological pause between books
        fsm.inject_pause()
        delay = bio_engine.generate_micro_jitter(2500.0) / 1000.0
        await asyncio.sleep(delay)
        fsm.resume_activity()

    fsm.conclude_session()
    await stealth.close()
    
    # Export fresh analytics
    exports = pipeline.export_analytics(config.storage.export_dir)
    logger.info(f"\n=======================================================")
    logger.info(f"MASSIVE REVIEW HARVESTING COMPLETED!")
    logger.info(f"Total reviews ingested across all books: {total_new_reviews_all_books}")
    logger.info(f"Export CSV: {exports['reviews_csv']}")
    logger.info(f"=======================================================\n")

if __name__ == "__main__":
    asyncio.run(run_massive_harvest())
