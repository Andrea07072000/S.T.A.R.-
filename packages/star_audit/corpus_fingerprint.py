"""Platform-independent fingerprint of an audit corpus: floats are rounded to 9 decimals before hashing, because the
C math library of different operating systems may differ in the last bit of sin/cos (2026-10-05: the raw-float hash of
the elements corpus differed between Windows and Linux). Usage: python corpus_fingerprint.py <module> -> sha256."""
import hashlib
import importlib
import json
import sys


def rounded(x, nd=9):
    if isinstance(x, float):
        return round(x, nd)
    if isinstance(x, list):
        return [rounded(v, nd) for v in x]
    if isinstance(x, dict):
        return {k: rounded(v, nd) for k, v in x.items()}
    return x


def fingerprint(corpus) -> str:
    return hashlib.sha256(json.dumps(rounded(corpus), sort_keys=True).encode()).hexdigest()


if __name__ == "__main__":
    print(fingerprint(importlib.import_module(sys.argv[1]).corpus()))
