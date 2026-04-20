#!/usr/bin/env python3
"""Stop the SNMP sandbox stack (Docker Compose) and clear local tcpdump artifacts."""

import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COMPOSE_FILE = os.path.join(SCRIPT_DIR, "compose.sandbox.yaml")


def main() -> None:
    cmd = [
        "docker",
        "compose",
        "-f",
        COMPOSE_FILE,
        "run",
        "--rm",
        "sandbox-cli",
        "down",
    ]
    print("Running:", " ".join(cmd))
    rc = subprocess.call(cmd, cwd=SCRIPT_DIR, env=os.environ)
    tcpdump_dir = os.path.join(SCRIPT_DIR, "tcpdump")
    os.makedirs(tcpdump_dir, exist_ok=True)
    for name in os.listdir(tcpdump_dir):
        if name == "README.md":
            continue
        path = os.path.join(tcpdump_dir, name)
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError:
            pass
    raise SystemExit(rc)


if __name__ == "__main__":
    main()
