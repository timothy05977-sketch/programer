"""Pytest fixtures — make shared + skill scripts importable."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "skills" / "monitor" / "scripts"))
sys.path.insert(0, str(ROOT / "skills" / "agent" / "scripts"))
