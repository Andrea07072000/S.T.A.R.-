# Security

## Reporting a vulnerability

Please report suspected vulnerabilities **privately** by email to cavazziniandrea515@gmail.com, not
in a public issue. Include what you observed, how to reproduce it, and the affected commit.
You will receive an acknowledgement; there is currently no formal response-time commitment.

## Scope

This repository contains a pure-Python library without network access, file writes (outside the
optional `verification/run_verification.py`, which writes only to `verification/evidence/`) or
runtime dependencies. The most relevant class of issue is an **incorrect result presented as valid**
(for example a wrong time offset returned instead of an error): please report those too.

## What this repository does not contain

No credentials, customer data or private infrastructure are part of this repository or its history.
If you find something that looks like one, please report it privately as above.
