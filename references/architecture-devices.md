# Data Center SNMP Sandbox – Architecture

This sandbox simulates a **real data center** for Datadog Network Device Monitoring. All SNMP metrics—topology, throughput, CPU, memory, and device-specific MIBs—are aligned with this architecture.

## Design Goal

The sandbox represents a production-style data center with:

- **Traffic flow**: Internet → Edge → Firewall → Load Balancer → Core → Leaf/SAN/Office
- **Inbound/outbound throughput**: Interface metrics scaled by tier (edge highest, access lower)
- **CPU & memory**: Role-appropriate utilization per device type
- **Topology**: LLDP/CDP links matching the physical layout
- **All SNMP metrics**: IF-MIB, HOST-RESOURCES, LLDP-MIB, vendor MIBs (Arista, Palo Alto, Cisco, F5, APC)

## Architecture Diagram

```
                              Internet
                                  |
                         +----------------+
                         |  Cisco ASR1001 |
                         |  Edge Router   |
                         +----------------+
                                  |
                      +------------------------+
                      | Palo Alto PA-3220 HA   |
                      | External Firewall Pair |
                      +------------------------+
                                  |
                         +------------------+
                         | F5 BIG-IP LTM    |
                         | (DMZ Load Bal.)  |
                         +------------------+
                                  |
                  =====================================
                  ||         Data Center Core        ||
                  =====================================
                   |                                |
         +------------------+             +------------------+
         | Arista 7280R     |-------------| Arista 7280R     |
         | Core Switch 1    |   MLAG      | Core Switch 2    |
         +------------------+             +------------------+
                   |                                |
            -------------------              -------------------
            |                 |              |                 |
     +---------------+  +---------------+    |         +-----------------+
     | Arista 7050X  |  | Arista 7050X  |    |         | Cisco MDS 9148 |
     | Leaf / ToR 1  |  | Leaf / ToR 2  |    |         | SAN Switch     |
     +---------------+  +---------------+    |         +-----------------+
                   |                                |
           Server Racks                    Fibre Channel

                        Office Distribution
                                |
                       +-------------------+
                       | Cisco Catalyst   |
                       | 9300 Access Stack|
                       +-------------------+
                                |
                    +-----------------------+
                    | Cisco 9800 WLC       |
                    | Wireless Controller  |
                    +-----------------------+
                                |
                              APs

                        Management Network
                                |
                       +------------------+
                       | APC AP8853 PDU   |
                       +------------------+
```

## Device Map (IP → Role)

| Device | IP | Role | Traffic Tier |
|--------|-----|------|--------------|
| Cisco ASR1001 | 172.20.0.10 | Edge Router | 1 (highest) |
| Palo Alto PA-3220 #1 | 172.20.0.11 | External Firewall (HA primary) | 2 |
| Palo Alto PA-3220 #2 | 172.20.0.12 | External Firewall (HA secondary) | 2 |
| F5 BIG-IP LTM | 172.20.0.13 | DMZ Load Balancer | 3 |
| Arista 7280R Core 1 | 172.20.0.14 | Data Center Core (MLAG) | 4 |
| Arista 7280R Core 2 | 172.20.0.15 | Data Center Core (MLAG) | 4 |
| Arista 7050X Leaf 1 | 172.20.0.16 | Leaf / ToR → Server Racks | 5 |
| Arista 7050X Leaf 2 | 172.20.0.17 | Leaf / ToR → Server Racks | 5 |
| Cisco MDS 9148 | 172.20.0.18 | SAN Switch (FC) | 6 |
| Cisco Catalyst 9300 | 172.20.0.19 | Office Distribution / Access | 5 |
| Cisco 9800 WLC | 172.20.0.20 | Wireless Controller | 6 |
| APC AP8853 PDU | 172.20.0.21 | Management / Power | 7 |

## Topology (LLDP/CDP)

| Device | Neighbors |
|--------|-----------|
| ASR1001 | Palo Alto 1, Palo Alto 2 |
| Palo Alto 1/2 | ASR1001, F5 |
| F5 | Palo Alto 1, Palo Alto 2, Core 1, Core 2 |
| Core 1 | F5, Core 2 (MLAG), Leaf 1, MDS, Catalyst 9300 |
| Core 2 | F5, Core 1 (MLAG), Leaf 2, MDS, Catalyst 9300 |
| Leaf 1 | Core 1 |
| Leaf 2 | Core 2 |
| MDS 9148 | Core 1, Core 2 |
| Catalyst 9300 | Core 1, Core 2, 9800 WLC, APC PDU |
| 9800 WLC | Catalyst 9300 |
| APC PDU | Catalyst 9300 |

## Interface-to-Interface Links (Direct Topology)

Each link is a direct connection: `Device A / Interface ↔ Device B / Interface`.

| Link | Device A | If | Device B | If |
|------|----------|-----|----------|-----|
| Edge→Firewall | ASR1001 | A1 | Palo Alto 1 | A1 |
| Edge→Firewall | ASR1001 | A2 | Palo Alto 2 | A1 |
| Firewall→LB | Palo Alto 1 | A2 | F5 | A1 |
| Firewall→LB | Palo Alto 2 | A2 | F5 | A2 |
| LB→Core | F5 | A3 | Core 1 | A1 |
| LB→Core | F5 | A4 | Core 2 | A1 |
| MLAG | Core 1 | A2 | Core 2 | A2 |
| Core→Leaf | Core 1 | A3 | Leaf 1 | A1 |
| Core→Leaf | Core 2 | A3 | Leaf 2 | A1 |
| Core→SAN | Core 1 | A4 | MDS 9148 | A1 |
| Core→SAN | Core 2 | A4 | MDS 9148 | A2 |
| Core→Office | Core 1 | A5 | Catalyst 9300 | A1 |
| Core→Office | Core 2 | A5 | Catalyst 9300 | A2 |
| Office→WLC | Catalyst 9300 | A3 | 9800 WLC | A1 |
| Office→PDU | Catalyst 9300 | A4 | APC PDU | A1 |

## Throughput (ifHCInOctets / ifHCOutOctets)

Interface byte counters are tiered to reflect data center traffic flow (Internet → Edge → … → PDU):

| Tier | Role | Approx. byte counters (SI, on LLDP-facing ifIndex rows) |
|------|------|--------------------------------------------------------|
| 1 | Edge | ~1.2×10¹¹ |
| 2 | Firewall | ~9×10¹⁰ |
| 3 | Load Balancer | ~7×10¹⁰ |
| 4 | Core | ~5.5×10¹⁰ |
| 5 | Leaf / Access | ~2.5×10¹⁰ |
| 6 | SAN / WLC | ~1.2×10¹⁰ |
| 7 | PDU | ~2×10⁹ |

Values scale simulated `ifHCInOctets` / `ifHCOutOctets` (and matching 32-bit `ifInOctets` / `ifOutOctets` where present).

Topology interfaces (ports with LLDP neighbors) use these values; other interfaces inherit from the base data.

## Quick Test

From the `snmp/` directory:

```bash
./snmpwalk_device.sh cisco-asr1001 system
./snmpwalk_device.sh 172.20.0.10 system
```

Or from inside the Docker network (e.g. Datadog agent):

```bash
snmpwalk -v2c -c mocksnmp 172.20.0.10 system
```

> **Note:** On Docker Desktop for Mac, host→container UDP port forwarding can be unreliable. Use `snmpwalk_device.sh` (runs from a container on the same network) or the Datadog agent for reliable SNMP queries.

## Host Port Map (for snmpwalk from host)

| Device | Host Port |
|--------|-----------|
| Cisco ASR1001 | 11610 |
| Palo Alto #1 | 11611 |
| Palo Alto #2 | 11612 |
| F5 BIG-IP | 11613 |
| Arista Core 1 | 11614 |
| Arista Core 2 | 11615 |
| Arista Leaf 1 | 11616 |
| Arista Leaf 2 | 11617 |
| Cisco MDS | 11618 |
| Cisco Catalyst | 11619 |
| Cisco 9800 WLC | 11620 |
| APC PDU | 11621 |

## MIB Coverage

- **IF-MIB** – Interface speed, status, traffic (ifHCInOctets, ifHCOutOctets, ifSpeed, etc.)
- **HOST-RESOURCES-MIB** – CPU usage, memory total/used
- **LLDP-MIB** – Topology (lldpRemTable, lldpLocPortTable)
- **CISCO-CDP-MIB** – Cisco neighbor discovery
- **PAN-COMMON-MIB** – Palo Alto session utilization
- **ENTITY-MIB** / **ENTITY-SENSOR-MIB** – Arista chassis/sensor metadata
- **ARISTA-QUEUE-MIB** – Ingress/egress queue stats
- **APC** – PDU load, outlet status

**Datadog**: Use generic autodiscovery (172.20.0.0/24); devices match vendor profiles by sysObjectID. See [DATADOG_AGENT_DEPLOYMENT.md](DATADOG_AGENT_DEPLOYMENT.md) for deployment steps.
