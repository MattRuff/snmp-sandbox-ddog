# Datadog Network Device Monitoring – Metrics Guide

This guide helps you find and visualize the most useful SNMP metrics in the Datadog UI for this sandbox. The sandbox uses **generic autodiscovery** (no custom config); configure your agent to discover 172.20.0.0/24.

## Profile Mapping (Autodiscovery)

Devices are matched by `sysObjectID` to Datadog vendor profiles:

| Device | Profile | Key Metrics |
|--------|---------|-------------|
| Cisco ASR1001 | cisco-asr | CPU, memory, interfaces, BGP |
| Palo Alto PA-3220 | palo-alto | CPU, memory, interfaces, **panSessionUtilization**, **panSessionActive** |
| F5 BIG-IP LTM | f5-big-ip | CPU, memory, interfaces, F5-specific |
| Arista 7280R/7050X | arista | CPU, memory, interfaces, **entPhySensorTable** (temp), BGP |
| Cisco MDS 9148 | cisco-nexus | CPU, memory, interfaces |
| Cisco Catalyst 9300 | cisco-catalyst | CPU, memory, interfaces |
| Cisco 9800 WLC | cisco-catalyst-wlc | CPU, memory, interfaces, wireless clients |
| APC AP8853 PDU | apc-pdu | **powernet.rPDULoadStatusLoad**, outlet status |

## Metrics to Monitor in the Datadog UI

### 1. **CPU & Memory (All Devices)**

| Metric | Description | Typical Range | Where to Find |
|--------|-------------|---------------|---------------|
| `snmp.cpu.usage` | CPU utilization % | Routers: 15–25%, Firewalls: 25–35%, Switches: 5–15% | Metrics → `snmp.cpu.usage` |
| `snmp.memory.total` | Total memory (bytes) | Varies by device | Metrics → `snmp.memory.total` |
| `snmp.memory.used` | Used memory (bytes) | Varies by device | Metrics → `snmp.memory.used` |

**Dashboard query example:**
```
avg:snmp.cpu.usage{*} by {snmp_host}
```

### 2. **Interface Metrics**

| Metric | Description | Use Case |
|--------|-------------|----------|
| `snmp.ifHCInOctets.rate` | Inbound bytes/sec | Bandwidth utilization |
| `snmp.ifHCOutOctets.rate` | Outbound bytes/sec | Bandwidth utilization |
| `snmp.ifSpeed` | Interface speed (bps) | Capacity planning |
| `snmp.ifAdminStatus` | Admin status (1=up, 2=down) | Link status |
| `snmp.ifOperStatus` | Operational status | Link health |
| `snmp.ifInErrors.rate` | Inbound errors | Troubleshooting |
| `snmp.ifOutErrors.rate` | Outbound errors | Troubleshooting |

**Dashboard query example:**
```
avg:snmp.ifHCInOctets.rate{*} by {snmp_host,interface}
```

### 3. **Palo Alto Firewall (Device-Specific)**

| Metric | Description | Typical Range |
|--------|-------------|---------------|
| `snmp.panSessionUtilization` | Session table utilization % | 20–60% normal |
| `snmp.panSessionActive` | Active sessions | Varies by traffic |
| `snmp.panSessionMax` | Max session capacity | Static |

### 4. **Arista Switches (Device-Specific)**

| Metric | Description |
|--------|-------------|
| `snmp.entPhySensorValue` | Temperature, power sensors |
| `snmp.aristaIfInOctetRate` | Interface inbound rate (Arista MIB) |
| `snmp.aristaIfOutOctetRate` | Interface outbound rate |

### 5. **APC PDU (Device-Specific)**

| Metric | Description |
|--------|-------------|
| `snmp.powernet.rPDULoadStatusLoad` | Load per phase/bank |
| `snmp.powernet.rPDUOutletStatusLoad` | Per-outlet load |

### 6. **LLDP Topology**

The `snmp.lldpRem` metric (with tag `lldp_rem_sys_name`) powers the **Device Topology Map**. Use the Network Device Monitoring → Topology view to see device relationships.

## Sandbox Simulated Values (Typical)

| Device Type | CPU % | Memory Used | Notes |
|-------------|-------|-------------|-------|
| Edge router (ASR) | 22% | ~6GB / 8GB | BGP, routing |
| Firewall (Palo Alto) | 26–28% | ~9–10GB / 16GB | Session inspection |
| Load balancer (F5) | 18% | ~9GB / 16GB | Connection handling |
| Core switch (Arista 7280) | 11–12% | ~4GB / 8GB | High throughput |
| Leaf switch (Arista 7050) | 7–8% | ~2GB / 4GB | Access layer |
| SAN switch (MDS) | 4% | ~1.5GB / 4GB | FC switching |
| Access switch (Catalyst) | 10% | ~3GB / 8GB | Port density |
| WLC (9800) | 25% | ~5GB / 8GB | AP management |
| PDU (APC) | 2% | ~200MB / 512MB | Minimal compute |

## Building a Dashboard

1. **Network → Devices** – Use the built-in NDM device list and topology map.
2. **Dashboards → New Dashboard** – Create a custom dashboard.
3. **Add widgets:**
   - **Timeseries**: `avg:snmp.cpu.usage{*} by {snmp_host}`
   - **Timeseries**: `avg:snmp.memory.used{*} by {snmp_host}` (or `sum` for total)
   - **Query**: Filter by `device:cisco-asr1001` or `role:firewall` using your tags.
4. **Topology Map**: Network → Devices → Topology (requires LLDP data).

## Useful Filters

- `snmp_host:edge-router-asr1001` – By device hostname
- `device:cisco-asr1001` – By device tag
- `role:firewall` – By role
- `interface:eth0` – By interface name

## References

- [Datadog SNMP Metrics](https://docs.datadoghq.com/network_monitoring/devices/data/)
- [Supported Devices](https://docs.datadoghq.com/network_monitoring/devices/supported_devices)
- [Device Topology Map](https://docs.datadoghq.com/network_monitoring/devices/guide/)
