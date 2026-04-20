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
| **Python 3.11.x** | e.g. `pyenv install 3.11.9` and `pyenv local 3.11.9` in this repo |
| **Wireshark** (optional) | `brew install --cask wireshark` |
| **Datadog Agent** | Host agent optional; SNMP autodiscovery uses the **Docker** agent in `snmp/docker-compose.yaml` |

---

## Quick start

```bash
git clone <your-fork-or-repo-url>.git
cd snmp_sandbox_ddog   # or your clone directory name

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cd snmp
cp .env.example .env
# Edit .env: set DD_API_KEY (see references/DATADOG_AGENT_DEPLOYMENT.md)

# Start simulators + agent (from repo root or follow SANDBOX_WORKFLOW.md)
```

Pre-built SNMP simulator images default to **`matthewruyffelaert667/snmp-sandbox-sim:latest`** on Docker Hub (`SNMP_SIM_IMAGE` overrides). Pass **`DD_API_KEY`** via `snmp/.env`, `export`, or compose environment. Details: [references/DATADOG_AGENT_DEPLOYMENT.md](references/DATADOG_AGENT_DEPLOYMENT.md).

---

## More docs

- [references/TROUBLESHOOTING_SNMP.md](references/TROUBLESHOOTING_SNMP.md)  
- [references/DATADOG_METRICS_GUIDE.md](references/DATADOG_METRICS_GUIDE.md)  

---

## Credits

- Original [SNMP-Sandbox](https://github.com/prerakdali/SNMP-Sandbox) — creator: **Brian Hartford**  
- Updates and extensions: **Matthew Ruyffelaert**
