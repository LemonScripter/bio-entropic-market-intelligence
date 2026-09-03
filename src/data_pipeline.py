"""
Module 4: Persistence, State Management, and Market Data Pipeline

Implements:
1. SQLite relational database schema for products, price history, reviews, and competitive intelligence.
2. Robust parsing pipeline (lxml / BeautifulSoup) with defensive extraction fallback.
3. Export functionality for structured JSON/CSV analytics downstream.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import sqlite3
import json
import logging
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup

logger = logging.getLogger("DataPipeline")


class MarketDataPipeline:
    """
    Manages structured ingestion, deduplication, schema migrations,
    and analytic exports for market intelligence entities.
    """

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes SQLite tables for products, price snapshots, and customer feedback."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Products Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    asin TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    brand TEXT,
                    rating REAL,
                    ratings_count INTEGER,
                    canonical_url TEXT,
                    prime_eligible INTEGER,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Price History Snapshots Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asin TEXT NOT NULL,
                    price REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    availability TEXT,
                    snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (asin) REFERENCES products(asin)
                )
            """)

            # Reviews & Sentiment Data Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id TEXT PRIMARY KEY,
                    asin TEXT NOT NULL,
                    reviewer_name TEXT,
                    rating REAL NOT NULL,
                    title TEXT,
                    body TEXT,
                    verified_purchase INTEGER,
                    review_date TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (asin) REFERENCES products(asin)
                )
            """)
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def parse_product_card_html(self, html_content: str, category: str = "general") -> List[Dict[str, Any]]:
        """
        Parses Amazon-style SERP product cards using robust heuristic selectors.
        """
        soup = BeautifulSoup(html_content, "lxml")
        items = []

        # Target search result cards
        cards = soup.select('div[data-component-type="s-search-result"]')
        for card in cards:
            try:
                asin = card.get("data-asin", "").strip()
                if not asin:
                    continue

                # Title Extraction
                title_elem = card.select_one("h2 a span") or card.select_one("h2 span")
                title = title_elem.get_text(strip=True) if title_elem else "Unknown Product"

                # URL Extraction
                link_elem = card.select_one("h2 a")
                canonical_url = ("https://www.amazon.com" + link_elem["href"]) if (link_elem and link_elem.get("href")) else ""

                # Price Extraction
                price_whole = card.select_one(".a-price-whole")
                price_fraction = card.select_one(".a-price-fraction")
                price = 0.0
                if price_whole:
                    whole_str = price_whole.get_text(strip=True).replace(",", "").replace(".", "")
                    frac_str = price_fraction.get_text(strip=True) if price_fraction else "00"
                    try:
                        price = float(f"{whole_str}.{frac_str}")
                    except ValueError:
                        price = 0.0

                # Rating Extraction
                rating = 0.0
                rating_elem = card.select_one('i[class*="a-star-"] span')
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    try:
                        rating = float(rating_text.split()[0])
                    except (ValueError, IndexError):
                        rating = 0.0

                # Review Count
                ratings_count = 0
                count_elem = card.select_one('span[aria-label*="ratings"]') or card.select_one('a[href*="#customerReviews"] span')
                if count_elem:
                    raw_count = count_elem.get_text(strip=True).replace(",", "").replace(".", "")
                    if raw_count.isdigit():
                        ratings_count = int(raw_count)

                # Prime Badge
                prime_eligible = 1 if card.select_one('i[aria-label="Amazon Prime"]') else 0

                product_data = {
                    "asin": asin,
                    "title": title,
                    "brand": "Generic",
                    "rating": rating,
                    "ratings_count": ratings_count,
                    "canonical_url": canonical_url,
                    "prime_eligible": prime_eligible,
                    "category": category,
                    "current_price": price,
                    "availability": "In Stock" if price > 0 else "Unavailable"
                }
                items.append(product_data)
            except Exception as e:
                logger.debug(f"Failed parsing single product card: {e}")
                continue

        logger.info(f"Extracted {len(items)} structured product items from HTML snippet.")
        return items

    def ingest_product(self, product: Dict[str, Any]):
        """Persists or updates product records and appends price history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Upsert product record
            cursor.execute("""
                INSERT INTO products (asin, title, brand, rating, ratings_count, canonical_url, prime_eligible, category, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(asin) DO UPDATE SET
                    title=excluded.title,
                    rating=excluded.rating,
                    ratings_count=excluded.ratings_count,
                    canonical_url=excluded.canonical_url,
                    prime_eligible=excluded.prime_eligible,
                    category=excluded.category,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                product["asin"],
                product["title"],
                product.get("brand", "Generic"),
                product.get("rating", 0.0),
                product.get("ratings_count", 0),
                product.get("canonical_url", ""),
                product.get("prime_eligible", 0),
                product.get("category", "general")
            ))

            # Insert price snapshot if price is positive
            if product.get("current_price", 0.0) > 0:
                cursor.execute("""
                    INSERT INTO price_history (asin, price, currency, availability)
                    VALUES (?, ?, ?, ?)
                """, (
                    product["asin"],
                    product["current_price"],
                    product.get("currency", "USD"),
                    product.get("availability", "In Stock")
                ))

            conn.commit()

    def ingest_batch(self, products: List[Dict[str, Any]]):
        """Batch ingestion helper."""
        for p in products:
            self.ingest_product(p)

    def export_analytics(self, export_dir: Path) -> Dict[str, Path]:
        """Generates structured CSV and JSON exports for analytical downstream pipelines."""
        export_dir = Path(export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = export_dir / f"market_intelligence_{timestamp}.csv"
        json_path = export_dir / f"market_intelligence_{timestamp}.json"

        with self._get_connection() as conn:
            df_products = pd.read_sql_query("""
                SELECT 
                    p.asin, p.title, p.brand, p.rating, p.ratings_count, 
                    p.category, p.prime_eligible, ph.price as latest_price, 
                    ph.snapshot_time as last_price_update
                FROM products p
                LEFT JOIN price_history ph ON p.asin = ph.asin
                GROUP BY p.asin
                ORDER BY p.updated_at DESC
            """, conn)

        df_products.to_csv(csv_path, index=False)
        df_products.to_json(json_path, orient="records", indent=2)

        logger.info(f"Analytics export generated:\n- CSV: {csv_path}\n- JSON: {json_path}")
        return {"csv": csv_path, "json": json_path}
