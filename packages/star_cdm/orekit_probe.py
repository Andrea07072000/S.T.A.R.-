"""Run inside WSL /root/orekit_venv: parse CCSDS CDM examples with Orekit and print JSON (independent oracle)."""
import json
import sys

import orekit_jpype as o
o.initVM()
from orekit_jpype.pyhelpers import setup_orekit_data  # noqa: E402
setup_orekit_data(filenames="/root/orekit-data.zip", from_pip_library=False)
from org.orekit.data import DataSource  # noqa: E402
from org.orekit.files.ccsds.ndm import ParserBuilder  # noqa: E402

out = {}
for path in sys.argv[1:]:
    try:
        cdm = ParserBuilder().buildCdmParser().parseMessage(DataSource(path))
        rel = cdm.getRelativeMetadata()
        o1 = cdm.getDataObject1()
        sv = o1.getStateVectorBlock()
        cov = o1.getRTNCovarianceBlock()
        out[path] = {"ok": True, "miss_m": float(rel.getMissDistance()), "tca": str(rel.getTca()),
                     "o1_x_m": float(sv.getPositionVector().getX()), "o1_zdot_ms": float(sv.getVelocityVector().getZ()),
                     "o1_ct_t": float(cov.getCtt()), "o2_name": str(cdm.getMetadataObject2().getObjectName())}
    except Exception as e:  # report, never hide
        out[path] = {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"}
print(json.dumps(out))
