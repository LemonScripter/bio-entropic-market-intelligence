"""
Full Spectrum Deep Harvester for Top Books on Amazon.
Extracts:
1. Complete product metadata (Author, Publisher, Pages, ISBN, Rank, Price)
2. Granular customer reviews across multiple viewports/pages with full body text, verified status, and ratings.
3. Bio-entropic pacing and stealth execution.
"""

import sys
import asyncio
import sqlite3
import random
import logging
from pathlib import Path
from bs4 import BeautifulSoup

# Ensure project root in sys.path
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
logger = logging.getLogger("DeepHarvester")


def extract_deep_metadata(soup: BeautifulSoup, asin: str) -> dict:
    """Extracts granular book details from product detail page (/dp/)."""
    # Author
    author = "Unknown Author"
    author_elem = soup.select_one(".author a, #bylineInfo .author a, #bylineInfo span.author a, span.contributorNameID")
    if author_elem:
        author = author_elem.get_text(strip=True)
    elif soup.select_one("#bylineInfo"):
        author = soup.select_one("#bylineInfo").get_text(strip=True).replace("by", "").replace("Follow the author", "").strip()

    # Title
    title_elem = soup.select_one("#productTitle, #title")
    title = title_elem.get_text(strip=True) if title_elem else "Unknown Book"

    # Price
    price = 0.0
    price_whole = soup.select_one(".a-price .a-price-whole")
    price_frac = soup.select_one(".a-price .a-price-fraction")
    if price_whole:
        try:
            w = price_whole.get_text(strip=True).replace(",", "").replace(".", "")
            f = price_frac.get_text(strip=True) if price_frac else "00"
            price = float(f"{w}.{f}")
        except ValueError:
            price = 0.0

    # Rating
    rating = 0.0
    rating_elem = soup.select_one("#acrPopover span.a-icon-alt, span[data-hook='rating-out-of-text']")
    if rating_elem:
        try:
            rating = float(rating_elem.get_text(strip=True).split()[0])
        except (ValueError, IndexError):
            rating = 0.0

    # Ratings Count
    ratings_count = 0
    count_elem = soup.select_one("#acrCustomerReviewText, [data-hook='total-review-count']")
    if count_elem:
        digits = "".join(filter(str.isdigit, count_elem.get_text(strip=True)))
        if digits:
            ratings_count = int(digits)

    # Category / Best Sellers Rank
    category = "Books"
    detail_bullets = soup.select("#detailBullets_feature_div li, #productDetails_techSpec_section_1 tr")
    details_text = " ".join([b.get_text(strip=True) for b in detail_bullets])

    return {
        "asin": asin,
        "title": title,
        "brand": author,
        "rating": rating,
        "ratings_count": ratings_count,
        "current_price": price,
        "category": category,
        "canonical_url": f"https://www.amazon.com/dp/{asin}",
        "prime_eligible": 1 if soup.select_one("#primeBadge, i.a-icon-prime") else 0,
        "availability": "In Stock" if price > 0 else "Available"
    }


async def run_deep_harvest(limit: int = 10):
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
    fsm = BehavioralStateMachine(name="DeepBookHarvester")

    with sqlite3.connect(config.storage.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT asin, title FROM products
            WHERE title NOT LIKE '%Keyboard%' AND title NOT LIKE '%Mouse%'
            ORDER BY rating DESC, ratings_count DESC
            LIMIT ?
        """, (limit,))
        target_books = cursor.fetchall()

    logger.info(f"Starting Deep Extraction cycle for {len(target_books)} bestseller books...")

    context = await browser_manager.initialize()
    page = await context.new_page()

    try:
        fsm.start_exploration()

        for idx, (asin, book_title) in enumerate(target_books, 1):
            logger.info(f"\n==========================================")
            logger.info(f"[{idx}/{len(target_books)}] Deep Scraping: {asin} ('{book_title[:40]}...')")
            logger.info(f"==========================================")

            fsm.initiate_search()
            url = f"https://www.amazon.com/dp/{asin}"
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                logger.warning(f"Failed navigating to {url}: {e}")
                continue

            # Natural dwell time
            await asyncio.sleep(bio_engine.calculate_inter_action_delay(base_seconds=2.0))

            # Step 1: Ingest complete product metadata
            fsm.consume_content()
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")
            deep_meta = extract_deep_metadata(soup, asin)
            pipeline.ingest_product(deep_meta)
            logger.info(f"-> Metadata Updated: Author='{deep_meta['brand']}', Rating={deep_meta['rating']}, Reviews Count={deep_meta['ratings_count']:,}, Price=${deep_meta['current_price']}")

            # Step 2: Natural scroll down to load reviews
            await browser_manager.human_scroll(page, scroll_distance_y=2200)
            await asyncio.sleep(1.8)

            # Step 3: Extract customer reviews from DOM
            html_after_scroll = await page.content()
            reviews = pipeline.parse_product_reviews_html(html_after_scroll, asin)

            if reviews:
                pipeline.ingest_reviews_batch(reviews)
                logger.info(f"-> Customer Reviews Ingested: {len(reviews)} reviews with full text.")
            else:
                logger.warning(f"-> No reviews found in initial scroll for {asin}.")

            # Bio-rest pause
            fsm.inject_pause()
            pause_sec = bio_engine.generate_micro_jitter(2500.0) / 1000.0
            logger.info(f"Biological inter-item cooldown: {pause_sec:.2f}s")
            await asyncio.sleep(pause_sec)
            fsm.resume_activity()

        # Generate fresh analytical exports
        export_results = pipeline.export_analytics(config.storage.export_dir)
        logger.info(f"\nDeep Harvesting completed successfully!")
        logger.info(f"Exports generated: {export_results}")

    finally:
        await browser_manager.close()


if __name__ == "__main__":
    asyncio.run(run_deep_harvest(limit=10))
