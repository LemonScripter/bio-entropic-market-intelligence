"""
CLI Entry Point for the Bio-Entropic Web Data Collection & Market Analysis Framework.
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import AppConfig
from src.orchestrator import BioEntropicOrchestrator


def main():
    parser = argparse.ArgumentParser(
        description="Bio-Entropic Web Data Collection & Market Analysis Framework"
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=["mechanical keyboard wireless", "ergonomic mouse"],
        help="Search keywords to analyze"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Max pages per keyword query"
    )

    args = parser.parse_args()

    config = AppConfig.load_default()
    if args.headless:
        config.browser.headless = True

    orchestrator = BioEntropicOrchestrator(config)
    asyncio.run(orchestrator.run_market_observation_session(args.keywords, max_pages_per_kw=args.pages))


if __name__ == "__main__":
    main()
