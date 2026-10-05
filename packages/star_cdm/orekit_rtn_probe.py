"""Independent check of star_cdm.deep_consistency's RTN projection: Orekit 13.1 LOFType.QSW (radial / along-track /
cross-track, i.e. CCSDS RTN) built from object 1's inertial state; position of object 2 expressed in it. Run in WSL with
the Orekit venv; prints JSON {example: [R, T, N] in metres}. Reads the corrected CCSDS 508.0-B examples."""
import json
import re
import sys

import orekit_jpype
orekit_jpype.initVM()
from orekit_jpype.pyhelpers import setup_orekit_data  # noqa: E402
setup_orekit_data("/root/orekit-data.zip", from_pip_library=False)
from org.hipparchus.geometry.euclidean.threed import Vector3D  # noqa: E402
from org.orekit.frames import LOFType  # noqa: E402
from org.orekit.utils import PVCoordinates  # noqa: E402


def states(text):
    vals = {}
    obj = 0
    for line in text.splitlines():
        m = re.match(r"\s*(\w+)\s*=\s*([^\[]+)", line)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if k == "OBJECT":
            obj += 1
        if k in ("X", "Y", "Z", "X_DOT", "Y_DOT", "Z_DOT"):
            vals[(obj, k)] = float(v) * 1000.0
    pv = []
    for o in (1, 2):
        pv.append(PVCoordinates(Vector3D(vals[(o, "X")], vals[(o, "Y")], vals[(o, "Z")]),
                                Vector3D(vals[(o, "X_DOT")], vals[(o, "Y_DOT")], vals[(o, "Z_DOT")])))
    return pv


out = {}
for path in sys.argv[1:]:
    pv1, pv2 = states(open(path, encoding="utf-8").read())
    rot = LOFType.QSW.rotationFromInertial(pv1)
    d = rot.applyTo(pv2.getPosition().subtract(pv1.getPosition()))
    out[path.rsplit("/", 1)[-1]] = [d.getX(), d.getY(), d.getZ()]
print(json.dumps(out))
