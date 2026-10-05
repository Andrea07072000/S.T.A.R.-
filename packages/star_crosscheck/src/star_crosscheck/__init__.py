"""star_crosscheck — cross-solver verification fabric (S.T.A.R.)."""
from .core import AGREE, DEGRADED, DISAGREE, INSUFFICIENT, Engine, bundle_sha256, crosscheck

__version__ = "0.1.2"
__all__ = ["Engine", "crosscheck", "bundle_sha256", "AGREE", "DISAGREE", "INSUFFICIENT", "DEGRADED", "__version__"]
