# SNMP Sandbox Troubleshooting Guide

## Simulators (snmpsim containers)

Each device container runs **snmpsim** with a per-device `mocksnmp.snmprec` file. The community string is **`mocksnmp`** (filename `mocksnmp.snmprec`), matching `agent_config/datadog-docker.yaml` autodiscovery.

- **Healthcheck**: The image runs `/opt/snmpsim-healthcheck.py` (SNMP GET `sysDescr` on `127.0.0.1:161` with v2c + `mocksnmp`). Compose marks the service healthy only after snmpsim answers; the Datadog Agent waits for all simulators to be healthy before starting.
- **End-to-end check** (agent → lab IPs on the Docker network):

```bash
cd snmp && ./verify_simulators.sh
```

- **Rebuild the Hub image** after changing `snmp-healthcheck.py` or `Dockerfile.snmp_container` so pulls include the healthcheck.

## Connection Refused Errors

If you see agent logs like:
```
Error running check: check device reachable: failed: error reading from socket: 
read udp 172.20.0.2:XXXXX->172.20.0.10:161: recvfrom: connection refused
```

### Likely Causes

1. **Startup race condition** – The agent may scan the subnet before SNMP containers are fully listening. This often resolves within 1–2 minutes.
2. **SNMP containers not running** – Simulators must be up before the agent can collect.
3. **Agent not on SNMP network** – The agent must be attached to `snmp_static-network`.

### Quick Checks

```bash
# 1. Verify SNMP containers are running
cd snmp && docker compose ps

# 2. Verify agent is on the network
docker network inspect snmp_static-network --format '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}'
# Should show datadog-agent: 172.20.0.x/24

# 3. Test SNMP from inside the agent
docker exec datadog-agent agent snmp walk 172.20.0.10 -C mocksnmp | head -5

# 4. Check agent SNMP status
docker exec datadog-agent agent status | grep -A 3 "snmp"
```

### Fixes

| Issue | Fix |
|-------|-----|
| SNMP containers down | `cd snmp && docker compose up -d` |
| Agent not on network | `docker network connect snmp_static-network datadog-agent` |
| Both need restart | `cd snmp && docker compose restart` then `docker restart datadog-agent` |

---

## Host Cannot Reach 172.20.0.x Directly

The host is not on the Docker network. Use port mappings instead:

```bash
# From host: use 127.0.0.1 with mapped port
snmpwalk -v2c -c mocksnmp 127.0.0.1:11610 system   # cisco-asr1001
snmpwalk -v2c -c mocksnmp 127.0.0.1:11611 system   # paloalto-pa3220-1
# etc. (see architecture-devices.md for port list)
```

---

## Other Log Messages (Usually Harmless)

| Message | Meaning |
|--------|---------|
| `dial tcp [::1]:5001: connect: connection refused` | Internal agent IPC during startup; resolves when core agent is ready |
| `dial tcp 169.254.169.254:80: connect: connection refused` | EC2 metadata (not used in sandbox); safe to ignore |
| `Could not send payload: Post "...ndm-intake...": EOF` | Transient NDM intake issue; agent retries automatically |

---

## Device in Topology but Not in Device List

If a device (e.g. cisco-catalyst-9300-access) appears in the topology path (Core1 → Catalyst → Core2) but the Catalyst itself doesn't show in **Network → Devices**:

1. **Topology vs device**: Topology comes from LLDP (Core1/Core2 advertise their neighbor). The device list requires direct SNMP polling to succeed.
2. **Startup order**: The agent may scan before SNMP containers are ready. The compose now has `depends_on` so the agent starts after all devices.
3. **Profile OIDs**: The cisco-catalyst profile needs CISCO-STACK-MIB `chassisSerialNumberString`. The sandbox now includes this for the Catalyst.

**Verify Catalyst from agent:**
```bash
docker exec datadog-agent agent snmp walk 172.20.0.19 -C mocksnmp 1.3.6.1.2.1.1
```

---

## Topology Not Showing in Datadog

1. Ensure `collect_topology: true` in `agent_config/datadog-docker.yaml` (under `network_devices.autodiscovery.configs`).
2. Arista devices need `arista-switch` profile (LLDP); Cisco devices get CDP automatically.
3. Allow 5–15 minutes for topology data to appear in **Network → Devices → Topology**.
