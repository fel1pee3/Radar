import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "edge" / "src"))
sys.path.insert(0, str(ROOT / "experiments" / "directml"))
