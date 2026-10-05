"""Freezes independent references for star_orbit's GMST and Sun direction (run in the astropy venv; output
reference.json is committed). GMST: ERFA gmst82 (IAU 1982, UT1 taken = UTC here, as core.py does). Sun: astropy
get_sun (GCRS, apparent), unit vector. Epochs span 1990..2035 so the linear-in-d terms are exercised."""
import json
from pathlib import Path

import astropy
import erfa
import numpy as np
from astropy.coordinates import get_sun
from astropy.time import Time

EPOCHS = ["1990-03-21T06:00:00", "2000-01-01T12:00:00", "2010-07-15T18:30:00", "2024-12-21T00:00:00",
          "2030-06-01T09:15:00", "2035-11-11T23:59:00"]
out = {"source": f"erfa {erfa.__version__} gmst82; astropy {astropy.__version__} get_sun (GCRS)", "cases": []}
for e in EPOCHS:
    t = Time(e, scale="utc")
    g = float(np.degrees(erfa.gmst82(t.jd1, t.jd2)))
    s = get_sun(t).cartesian.xyz.value
    s = (s / np.linalg.norm(s)).tolist()
    out["cases"].append({"utc": e + "+00:00", "gmst82_deg": g, "sun_unit_gcrs": s})
Path(__file__).with_name("reference.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(out["source"], len(out["cases"]))
