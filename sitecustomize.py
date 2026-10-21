"""Make the project importable directly from the repository root."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
PACKAGE_DIR = ROOT / "prompt-optimizer-agent"

if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))
