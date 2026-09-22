---
name: LightGBM native runtime
description: The pinned LightGBM wheel needs the GCC OpenMP runtime available in the Replit Nix environment.
---

LightGBM 4.6.0 requires `libgomp.so.1`; the Python package can be installed while still failing at import if the Nix environment lacks `gcc` and `gcc-unwrapped`.

**Why:** The wheel loads a native shared library through `ctypes`, so a missing OpenMP runtime appears as an import-time `OSError`, not a Python dependency error.

**How to apply:** Keep the Nix package set used by this project provisioned with `gcc` and `gcc-unwrapped` before running GBM tests or model jobs.