# SNMP Sandbox – Workflow & Component Guide

This document explains how the sandbox components fit together and which workflows work with the current data center setup.

## Recommended Workflow (Current Setup)

```
1. Generate device data     →  snmp/generate_device_data.py
2. Start containers         →  docker compose -f compose.sandbox.yaml run --rm --build sandbox-cli
3. View in Datadog         →  Network → Devices, Topology
```

### Step-by-step

```bash
# 1. Regenerate SNMP data (topology, throughput, Arista MIBs, etc.)
cd snmp && python generate_device_data.py

# 2. Start containers (SNMP devices + Datadog Agent) — from repo root, no Python required:
export DD_API_KEY='<key>'   # or use snmp/.env
docker compose -f compose.sandbox.yaml run --rm --build sandbox-cli

# 3. Verify
docker exec datadog-agent agent status
# In Datadog: Network → Devices → Topology
```

Or use the menu: `python menu.py` → Option 2 (same as the `compose.sandbox.yaml` command above).

**Power user:** `cd snmp && docker compose up -d` (host Docker Compose, no wrapper image).

## Component Overview

| Component | Purpose | Status |
|-----------|---------|--------|
| **compose.sandbox.yaml** | Runs a small Docker CLI image that drives `snmp/docker-compose.yaml` via the host socket — primary way to start/stop without Python. | ✅ Active |
| **generate_device_data.py** | Creates per-device SNMP data from base mocksnmp.snmprec. Adds LLDP, CDP, Arista MIBs, throughput tiers. | ✅ Active |
| **docker-compose.yaml** | 12 SNMP device containers + Datadog Agent (datadog-agent) on 172.20.0.0/24. | ✅ Active |
| **agent_config/datadog-docker.yaml** | SNMP autodiscovery config mounted into datadog-agent. | ✅ Active |
| **menu.py** | Interactive menu for start, destroy, regenerate, compare OID. | ✅ Active |
| **start_sandbox.py** | Thin wrapper around `compose.sandbox.yaml` (optional). | ✅ Active |
| **destroy_sandbox.py** | Stops stack via the same CLI image, clears tcpdump files. | ✅ Active |
| **extract_oid.py** | Compares OIDs in a profile YAML to snmprec. | ✅ Active |

## Data Flow

```
snmp/data/mocksnmp.snmprec (base)
         │
         ▼
generate_device_data.py
         │
         ├──► snmp/data/cisco-asr1001/mocksnmp.snmprec
         ├──► snmp/data/paloalto-pa3220-1/mocksnmp.snmprec
         ├──► ... (one per device)
         └──► snmp/data/apc-ap8853-pdu/mocksnmp.snmprec
         │
         ▼
Simulator image (snmpsim data baked in) — see snmp/docker-compose.yaml
         │
         ▼
snmpsim serves SNMP on port 161
         │
         ▼
Datadog Agent (datadog-agent) polls 172.20.0.0/24
         │
         ▼
Datadog UI: Network → Devices, Topology, Metrics
```

## Network

- **Docker network**: `snmp_static-network` (from project `snmp` + network `static-network`)
- **Subnet**: 172.20.0.0/24
- **Agent**: Part of compose; attached to `static-network` automatically

## Quick Reference

| Task | Command |
|------|---------|
| Regenerate device data | `cd snmp && python generate_device_data.py` |
| Start stack (recommended) | `docker compose -f compose.sandbox.yaml run --rm --build sandbox-cli` |
| Stop stack | `docker compose -f compose.sandbox.yaml run --rm sandbox-cli down` |
| Start from `snmp/` (host) | `cd snmp && docker compose up -d` |
| SNMP check debug | `docker exec datadog-agent agent check snmp -l debug` |
| Walk a device | `cd snmp && ./snmpwalk_device.sh cisco-asr1001` |

## References

- [architecture-devices.md](architecture-devices.md) – Data center diagram, topology, throughput tiers
- [DATADOG_AGENT_DEPLOYMENT.md](DATADOG_AGENT_DEPLOYMENT.md) – Agent setup (compose-based)
- [TROUBLESHOOTING_SNMP.md](TROUBLESHOOTING_SNMP.md) – Common issues
