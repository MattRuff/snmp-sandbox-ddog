# Original SNMP Container Image (reference)

**Image:** `bhartford419/snmp_container:latest` / `bhartford419/snmp_container:arm64-latest`

This image has Python 3.12 compatibility issues with the bundled pysnmp library:
- `ModuleNotFoundError: No module named 'imp'` (removed in Python 3.12)
- `AttributeError: module 'importlib' has no attribute 'util'`

**Replacement:** Use the local build from `Dockerfile.snmp_container` which uses `snmpsim-lextudio` (Python 3.12 compatible).
