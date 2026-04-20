# Datadog Agent Deployment for SNMP Sandbox

The Datadog Agent is **included in docker-compose** and starts automatically with the SNMP containers.

## Prerequisites

The Datadog API key is **not** stored in any Docker image. You must supply `DD_API_KEY` when starting the stack.

**Option A — environment (recommended for the setup container or CI)**

```bash
export DD_API_KEY='<your_datadog_api_key>'
```

**Option B — local file (gitignored)**

```bash
cp snmp/.env.example snmp/.env
# Edit snmp/.env and set DD_API_KEY (do not commit snmp/.env)
```

Docker Compose reads `snmp/.env` for variable substitution into `docker-compose.yaml`.

**SNMP simulators** default to **`matthewruyffelaert667/snmp-sandbox-sim:latest`** on Docker Hub. Override with `export SNMP_SIM_IMAGE=...` if needed. After editing generated `snmp/data`, rebuild locally with `SNMP_SIM_IMAGE=snmp_container:local docker compose build cisco-asr1001` (then `up -d`).

**Setup container** — pass the key into the runner so compose sees it:

```bash
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$(pwd)":/work -w /work/snmp \
  -e DD_API_KEY \
  snmp-sandbox-setup compose up -d --no-build
```

(Requires `export DD_API_KEY=...` on the host first, or replace `-e DD_API_KEY` with `-e DD_API_KEY='...'`.)

## Automatic Installation

The agent starts when you run:

- **Option 2** from the menu (`python menu.py`)
- `python start_sandbox.py`
- Or directly: `cd snmp && docker compose up -d`

## Config

The agent uses `agent_config/datadog-docker.yaml`, mounted at `/etc/datadog-agent/datadog-docker.yaml`:

- SNMP autodiscovery on 172.20.0.0/24
- Community string: `mocksnmp`
- Topology collection enabled

## Host Requirements (macOS)

Create the agent run directory if it doesn't exist:

```bash
sudo mkdir -p /opt/datadog-agent/run
```

## Verification

- In Datadog: **Network → Devices** to see discovered devices
- Check agent status: `docker exec datadog-agent agent status`
- SNMP devices should appear with profiles matched by sysObjectID (cisco-asr, palo-alto, arista, etc.)

## Subnet

| Subnet        | Community   | Devices                    |
|---------------|-------------|----------------------------|
| 172.20.0.0/24 | mocksnmp    | 12 SNMP simulator devices   |
