"""Pytest configuration and shared fixtures for MarketLens test suite."""

from pathlib import Path
import sys

# Add src/ directory to sys.path so tests can import marketlens modules directly
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
