#!/usr/bin/env python3
"""Start the SNMP sandbox via the Docker CLI container (no stack logic here)."""

import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COMPOSE_FILE = os.path.join(SCRIPT_DIR, "compose.sandbox.yaml")


def main() -> None:
    if not _dd_api_key_configured():
        print(
            "DD_API_KEY is not set. Export it or add it to snmp/.env "
            "(copy from snmp/.env.example). Never commit API keys."
        )
        sys.exit(1)

    cmd = [
        "docker",
        "compose",
        "-f",
        COMPOSE_FILE,
        "run",
        "--rm",
        "--build",
        "sandbox-cli",
        "up",
    ]
    print("Running:", " ".join(cmd))
    raise SystemExit(subprocess.call(cmd, cwd=SCRIPT_DIR, env=os.environ))


def _dd_api_key_configured() -> bool:
    if os.environ.get("DD_API_KEY", "").strip():
        return True
    env_path = os.path.join(SCRIPT_DIR, "snmp", ".env")
    if not os.path.isfile(env_path):
        return False
    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("DD_API_KEY="):
                    return bool(line[len("DD_API_KEY=") :].strip().strip("'\""))
    except OSError:
        pass
    return False


if __name__ == "__main__":
    main()
