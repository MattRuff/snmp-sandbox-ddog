# SNMP sandbox (Datadog NDM)

Resources for **[The NDM/SNMP Detective’s sandbox: An interactive troubleshooting adventure](https://datadoghq.atlassian.net/wiki/spaces/TS/pages/4053663812/The+NDM+SNMP+Detective+s+sandbox+An+interactive+troubleshooting+adventure+WIP)**.

This project simulates a **small data center** for Datadog **Network Device Monitoring (NDM)**. SNMP metrics (topology, throughput, CPU, memory, vendor MIBs) follow a production-style layout:

- **Traffic flow:** Internet → edge router → firewall → load balancer → core → leaf / SAN / office  
- **Throughput:** Interface metrics scaled by tier (edge highest, PDU lowest)  
- **Topology:** LLDP/CDP aligned with the physical layout  

See [references/architecture-devices.md](references/architecture-devices.md) for the diagram and IP map. [references/SANDBOX_WORKFLOW.md](references/SANDBOX_WORKFLOW.md) describes generate → compose → agent and the menu entry points.

---

## Prerequisites

| Tool | Notes |
|------|--------|
| **Docker Desktop** (Mac) | Current version, daemon running |
| **Python 3.11.x** | Only for regenerating device data (`generate_device_data.py`) and optional `menu.py` |
| **Wireshark** (optional) | `brew install --cask wireshark` |
| **Datadog Agent** | Host agent optional; SNMP autodiscovery uses the **Docker** agent in `snmp/docker-compose.yaml` |

---

## Quick start (containers only)

From the **repository root** — builds a tiny Docker CLI image, then starts all SNMP simulators and the Datadog Agent on the **host** Docker daemon (socket-mounted):

```bash
git clone https://github.com/MattRuff/snmp-sandbox-ddog.git
cd snmp-sandbox-ddog

cp snmp/.env.example snmp/.env
# Edit snmp/.env: set DD_API_KEY (see references/DATADOG_AGENT_DEPLOYMENT.md)

docker compose -f compose.sandbox.yaml run --rm --build sandbox-cli
```

**Tear down:**

```bash
docker compose -f compose.sandbox.yaml run --rm sandbox-cli down
```

Pre-built SNMP simulator images default to **`matthewruyffelaert667/snmp-sandbox-sim:latest`** on Docker Hub (`SNMP_SIM_IMAGE` overrides). Pass **`DD_API_KEY`** via `snmp/.env` or `export`. Details: [references/DATADOG_AGENT_DEPLOYMENT.md](references/DATADOG_AGENT_DEPLOYMENT.md).

**Optional:** `python menu.py` or `python start_sandbox.py` call the same `compose.sandbox.yaml` flow. Regenerating MIB data still uses `cd snmp && python generate_device_data.py` (see [references/SANDBOX_WORKFLOW.md](references/SANDBOX_WORKFLOW.md)).

---

## More docs

- [references/TROUBLESHOOTING_SNMP.md](references/TROUBLESHOOTING_SNMP.md)  
- [references/DATADOG_METRICS_GUIDE.md](references/DATADOG_METRICS_GUIDE.md)  

---

## Credits

- Original [SNMP-Sandbox](https://github.com/prerakdali/SNMP-Sandbox) — creator: **Brian Hartford**  
- Updates and extensions: **Matthew Ruyffelaert**
