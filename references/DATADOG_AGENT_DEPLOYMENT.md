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

**Recommended — one container (no Python)** — from the **repository root**:

```bash
export DD_API_KEY='<your_datadog_api_key>'
docker compose -f compose.sandbox.yaml run --rm --build sandbox-cli
```

Or put the key in `snmp/.env` (same as Option B above); the CLI container reads it when it runs `docker compose` against `snmp/docker-compose.yaml`.

**Stop the stack:**

```bash
docker compose -f compose.sandbox.yaml run --rm sandbox-cli down
```

**Alternative — from `snmp/` on the host** (same Compose project, no wrapper image):

```bash
cd snmp && docker compose up -d
```

## Automatic Installation

The agent starts when you run any of:

- `docker compose -f compose.sandbox.yaml run --rm --build sandbox-cli` (recommended)
- **Option 2** from `python menu.py` (wraps the same command)
- `python start_sandbox.py` (same wrapper)
- Or: `cd snmp && docker compose up -d`

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
