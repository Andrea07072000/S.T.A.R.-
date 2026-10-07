# star_crosscheck — cross-solver verification fabric (S.T.A.R.)

Answers: *do engines of different lineage agree on this quantity, within a stated tolerance — and how independent are
they really?* Each engine declares its LINEAGE (model/data origin); same-lineage engines are one witness. Engines can
run in their own isolated venv (subprocess + JSON), so tools with conflicting dependencies are compared side by side.
Every run returns an evidence bundle with a sha256 over the result (timings excluded).

Verdicts: AGREE · DISAGREE · INSUFFICIENT_INDEPENDENCE · DEGRADED (a failed engine never counts as agreement).

## Requirements
- R1 `crosscheck(quantity, inputs, engines, tolerance, ...)` runs every engine (optionally in its own venv via subprocess
  + JSON) and returns a verdict: AGREE only if at least two DISTINCT lineages agree within the tolerance.
- R2 Engines of the same lineage count as ONE witness (INSUFFICIENT_INDEPENDENCE when fewer than two lineages remain).
- R3 A failed engine never counts as agreement: verdict DEGRADED, with the error recorded.
- R4 Optional published reference: every engine is also compared with it.
- R5 Every result is an evidence bundle with a sha256 over its content (timings excluded) — tamper-evident.

## Evidence so far
- Core: 7/7 tests; 3/3 mutants of the verification rules killed (lineage, failed engine, published reference).
- XC-001 geocentric Moon distance, 3 epochs, 5 engines in 5 venvs: SPICE = skyfield = jplephem (DE440) to 0,000 km;
  PyEphem 0,07–0,11 km; astropy builtin 1,5–38 km (tolerance 50 km) → AGREE.
  The campaign found two defects in OUR adapters before agreeing: SPICE time-string format, and a fixed
  TAI-UTC = 37 s (wrong in 2000: 32 s) that put jplephem 0,161 km away from the other DE440 engines.
  That is the product: a disagreement between same-lineage engines exposes an adaptation error, not physics.

## Adding an engine
`Engine(name, lineage, python=<venv python>, code="VERSION=...\ndef compute(inputs): ...")` — see
`campaign_moon_distance.py`.

## Changes
- 0.1.3 (2026-10-07): tests only. A corrected mutation measurement showed that no test would have failed on a wrong sign in the Euclidean
  distance of the 'norm' mode (the code was right; it was not pinned). Six guard tests added: the distance by hand, the verdict at the distance,
  zero tolerance, the default tolerance of a reference, the length of a recorded error, the rounding of the elapsed time.
