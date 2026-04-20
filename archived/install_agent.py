#!/usr/bin/env python3
"""Install and start the Datadog Agent for SNMP sandbox autodiscovery.
   Requires DD_API_KEY in environment or .env file."""

import os
import subprocess
import sys

AGENT_NAME = "dd-agent"
NETWORK_NAME = "snmp_static-network"
AGENT_RUN_DIR = "/opt/datadog-agent/run"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "agent_config", "datadog.yaml")
TCPDUMP_DIR = os.path.join(SCRIPT_DIR, "tcpdump")


def load_env():
    """Load .env if present (snmp/.env or .env)."""
    for name in ("snmp/.env", ".env"):
        env_path = os.path.join(SCRIPT_DIR, name)
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, val = line.partition("=")
                        os.environ[key.strip()] = val.strip().strip("'\"")
            break


def run(cmd, check=True):
    """Run shell command."""
    return subprocess.run(cmd, shell=True, check=check)


def agent_running():
    """Check if agent container exists and is running."""
    r = subprocess.run(
        f"docker ps -q -f name=^{AGENT_NAME}$",
        shell=True, capture_output=True, text=True
    )
    return bool(r.stdout.strip())


def agent_exists():
    """Check if agent container exists (running or stopped)."""
    r = subprocess.run(
        f"docker ps -aq -f name=^{AGENT_NAME}$",
        shell=True, capture_output=True, text=True
    )
    return bool(r.stdout.strip())


def network_exists():
    """Check if SNMP network exists."""
    r = subprocess.run(
        f"docker network ls -q -f name={NETWORK_NAME}",
        shell=True, capture_output=True, text=True
    )
    return bool(r.stdout.strip())


def main():
    load_env()
    api_key = os.environ.get("DD_API_KEY")
    if not api_key or api_key == "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX":
        print("Error: Set DD_API_KEY in environment or snmp/.env")
        print("  export DD_API_KEY=your_api_key")
        print("  Or add DD_API_KEY=your_api_key to snmp/.env")
        sys.exit(1)

    if not os.path.exists(CONFIG_PATH):
        print(f"Error: Config not found at {CONFIG_PATH}")
        sys.exit(1)

    # Ensure agent run dir exists (may need sudo on first run)
    if not os.path.exists(AGENT_RUN_DIR):
        print(f"Creating {AGENT_RUN_DIR} (may prompt for sudo)")
        run(f"sudo mkdir -p {AGENT_RUN_DIR}")

    # Ensure tcpdump dir exists for debug output
    os.makedirs(TCPDUMP_DIR, exist_ok=True)

    # Start SNMP containers first if not running (creates network)
    if not network_exists():
        print("Starting SNMP containers to create network...")
        run(f"cd {os.path.join(SCRIPT_DIR, 'snmp')} && docker compose up -d")
        import time
        time.sleep(3)

    if not network_exists():
        print(f"Error: Network {NETWORK_NAME} not found. Run: cd snmp && docker compose up -d")
        sys.exit(1)

    if agent_running():
        print(f"Agent {AGENT_NAME} already running")
        # Ensure connected to network
        r = subprocess.run(
            f"docker network inspect {NETWORK_NAME} --format '{{{{range .Containers}}}}{{{{.Name}}}}{{{{end}}}}'",
            shell=True, capture_output=True, text=True
        )
        if AGENT_NAME not in r.stdout:
            print(f"Connecting {AGENT_NAME} to {NETWORK_NAME}...")
            run(f"docker network connect {NETWORK_NAME} {AGENT_NAME}")
        return

    # Remove stopped container if exists
    if agent_exists():
        run(f"docker rm -f {AGENT_NAME}", check=False)

    print(f"Starting Datadog Agent ({AGENT_NAME})...")
    run(f"""docker run -d --name {AGENT_NAME} \
  -e DD_API_KEY={api_key} \
  -e DD_SITE="datadoghq.com" \
  -e DD_DOGSTATSD_NON_LOCAL_TRAFFIC=true \
  -e DD_LOGS_ENABLED=true \
  -e DD_LOGS_CONFIG_AUTO_MULTI_LINE_DETECTION=true \
  -e DD_LOGS_CONFIG_CONTAINER_COLLECT_ALL=true \
  -e DD_CONTAINER_EXCLUDE_LOGS="name:{AGENT_NAME}" \
  -v {AGENT_RUN_DIR}:/opt/datadog-agent/run:rw \
  -v {CONFIG_PATH}:/etc/datadog-agent/datadog.yaml:ro \
  -v {TCPDUMP_DIR}:/tcpdumps:rw \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /proc/:/host/proc/:ro \
  -v /sys/fs/cgroup/:/host/sys/fs/cgroup:ro \
  -v /var/lib/docker/containers:/var/lib/docker/containers:ro \
  registry.datadoghq.com/agent:7""")

    print(f"Connecting {AGENT_NAME} to {NETWORK_NAME}...")
    run(f"docker network connect {NETWORK_NAME} {AGENT_NAME}")

    print(f"Agent started. Check: docker exec {AGENT_NAME} agent status")
    print("Devices: Datadog → Network → Devices")


if __name__ == "__main__":
    main()
