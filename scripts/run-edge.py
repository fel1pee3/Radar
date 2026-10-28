"""Run the existing worker CLI in the selected isolated uv environment."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services/edge/src"))

from radar_edge.cli import main

if __name__ == "__main__":
    main()
