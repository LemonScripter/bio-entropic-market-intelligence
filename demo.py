"""
Bio-Entropic Automation Engine - Comprehensive Self-Test & Diagnostic Demo.

Runs a fast demonstration of:
1. Bio-Entropic Circadian & Micro-Jitter generation.
2. Mathematical Bézier trajectory path computation with velocity profiling.
3. Behavioral FSM transitions and state logging.
4. SQLite structured data ingestion and export.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import AppConfig
from src.bio_engine import BioEntropyEngine
from src.behavioral_motor import BezierTrajectoryGenerator, BehavioralStateMachine
from src.data_pipeline import MarketDataPipeline


def run_diagnostics():
    print("=" * 70)
    print("  BIO-ENTROPIC AUTOMATION & MARKET INTELLIGENCE FRAMEWORK")
    print("  System Self-Test & Operational Diagnostics")
    print("=" * 70)

    # 1. Test Configuration & Directories
    print("\n[Phase 1] Initializing Configuration and Local Data Storage...")
    config = AppConfig.load_default()
    print(f"  -> SQLite DB Target: {config.storage.db_path}")
    print(f"  -> Session Store Target: {config.browser.storage_state_path}")
    print(f"  -> Telemetry Cache: {config.bio.telemetry_csv_path}")

    # 2. Test Bio-Entropic Engine
    print("\n[Phase 2] Evaluating Bio-Entropic Timing & Telemetry Engine...")
    bio = BioEntropyEngine(
        telemetry_file=config.bio.telemetry_csv_path,
        macro_cycle_hours=168,
        active_threshold=0.45
    )
    state = bio.get_current_bio_state()
    print(f"  -> Macro State: {state['macro_state']}")
    print(f"  -> Biological Activity Index: {state['activity_index']:.4f}")
    print(f"  -> Circadian Cycle Hour (0-168h): {state['cycle_hour']:.2f}h")
    
    sample_jitters = [bio.generate_micro_jitter(100.0) for _ in range(5)]
    print(f"  -> Sample Micro-Jitter Delays (base 100ms): {sample_jitters} ms")

    # 3. Test Bézier Trajectory Generation
    print("\n[Phase 3] Generating Human-Like Bézier Cursor Trajectory...")
    start_point = (100.0, 200.0)
    target_point = (850.0, 620.0)
    trajectory = BezierTrajectoryGenerator.generate_path(
        start_pos=start_point,
        end_pos=target_point,
        points_count=20,
        deviation_scale=0.25,
        noise_level=0.8
    )
    print(f"  -> Trajectory points calculated: {len(trajectory)}")
    print(f"  -> Start: ({trajectory[0][0]:.1f}, {trajectory[0][1]:.1f})")
    print(f"  -> Midpoint: ({trajectory[len(trajectory)//2][0]:.1f}, {trajectory[len(trajectory)//2][1]:.1f})")
    print(f"  -> Target: ({trajectory[-1][0]:.1f}, {trajectory[-1][1]:.1f})")

    # 4. Test Stochastic State Machine
    print("\n[Phase 4] Verifying Behavioral FSM Lifecycle...")
    fsm = BehavioralStateMachine(name="DiagnosticUnit")
    print(f"  -> Initial State: {fsm.state}")
    fsm.start_exploration()
    print(f"  -> State after start_exploration: {fsm.state}")
    fsm.initiate_search()
    print(f"  -> State after initiate_search: {fsm.state}")
    fsm.consume_content()
    print(f"  -> State after consume_content: {fsm.state}")
    fsm.inject_pause()
    print(f"  -> State after inject_pause: {fsm.state}")
    fsm.resume_activity()
    print(f"  -> State after resume_activity: {fsm.state}")
    fsm.conclude_session()
    print(f"  -> Final State: {fsm.state}")

    # 5. Test Data Pipeline & Storage Ingestion
    print("\n[Phase 5] Testing Market Data Ingestion & Analytics Export...")
    pipeline = MarketDataPipeline(config.storage.db_path)
    
    sample_products = [
        {
            "asin": "B09W2DF485",
            "title": "Bio-Entropic Ergonomic Split Mechanical Keyboard",
            "brand": "ErgoTech",
            "rating": 4.8,
            "ratings_count": 1420,
            "canonical_url": "https://www.amazon.com/dp/B09W2DF485",
            "prime_eligible": 1,
            "category": "mechanical keyboard wireless",
            "current_price": 189.99,
            "currency": "USD",
            "availability": "In Stock"
        },
        {
            "asin": "B08N5LNQCX",
            "title": "Precision Vertical Wireless Mouse with Thumb Rest",
            "brand": "LogiPro",
            "rating": 4.6,
            "ratings_count": 8390,
            "canonical_url": "https://www.amazon.com/dp/B08N5LNQCX",
            "prime_eligible": 1,
            "category": "ergonomic mouse",
            "current_price": 69.99,
            "currency": "USD",
            "availability": "In Stock"
        }
    ]
    pipeline.ingest_batch(sample_products)
    print(f"  -> Successfully ingested {len(sample_products)} sample product records into SQLite.")
    
    exports = pipeline.export_analytics(config.storage.export_csv_dir)
    print(f"  -> Exported CSV: {exports['csv']}")
    print(f"  -> Exported JSON: {exports['json']}")

    print("\n" + "=" * 70)
    print("  ALL SUBSYSTEM DIAGNOSTICS COMPLETED SUCCESSFULLY [STATUS: OK]")
    print("=" * 70)


if __name__ == "__main__":
    run_diagnostics()
