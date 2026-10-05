"""Put this package's own src/ first on sys.path, so the tests (and mutation runs on a copied tree) exercise THIS source,
never an installed copy (2026-10-05: without it a mutant of a copied tree would have been tested against the original)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
