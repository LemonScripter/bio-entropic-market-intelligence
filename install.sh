#!/usr/bin/env bash
set -e

echo "========================================================"
echo "  Bio-Entropic Market Analysis Framework - Setup"
echo "========================================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH."
    exit 1
fi

echo "[1/3] Creating virtual environment (.venv)..."
python3 -m venv .venv
source .venv/bin/activate

echo "[2/3] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[3/3] Installing Playwright Chromium browser binaries..."
playwright install chromium

echo ""
echo "========================================================"
echo "  Installation completed successfully!"
echo "  To run diagnostics:  python demo.py"
echo "  To start collection: python main.py"
echo "========================================================"
echo ""
