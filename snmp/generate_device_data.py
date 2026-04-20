#!/usr/bin/env python3
"""Generate device-specific SNMP data from base mocksnmp.snmprec.
Includes LLDP (all devices) and CDP (Cisco devices) for topology discovery.

SNMP modelling conventions applied here:
- sysObjectID matches vendor/product family; sysDescr aligns with that identity.
- sysUpTime uses ASN.1 TimeTicks (snmpsim type 67), not a string.
- HOST-RESOURCES memory: used ≤ total; CPU load 0–100.
- ifHC* 64-bit counters paired with 32-bit ifInOctets/ifOutOctets on the same ifIndex
  (32-bit values clamped to 2^32−1 when HC exceeds Counter32 range).
- Palo Alto session utilization is derived from active/max unless overridden.
- CDP neighbor fields use per-platform version strings and plausible remote port IDs.
"""

import os

# LLDP-MIB OID base: 1.0.8802.1.1.2.1.4.1.1 (lldpRemEntry)
# Index: TimeMark.LocalPortNum.RemIndex (0.1.1 = first neighbor on port 1)
LLDP_REM_BASE = "1.0.8802.1.1.2.1.4.1.1"
# lldpLocPortTable: maps lldpLocPortNum to interface (agent needs this for interface-by-interface topology)
# OIDs: lldpLocPortNum.1.1, lldpLocPortIdSubtype.1.2, lldpLocPortId.1.3, lldpLocPortDesc.1.4
LLDP_LOC_PORT_BASE = "1.0.8802.1.1.2.1.3.7.1"
# ENTITY-MIB index 1 (chassis) - Arista metadata
ENTITY_PHYS_BASE = "1.3.6.1.2.1.47.1.1.1.1"
# ENTITY-SENSOR-MIB entPhySensorTable (base.column.index)
ENT_PHY_SENSOR_BASE = "1.3.6.1.2.1.99.1.1.1.1"
# ARISTA-QUEUE-MIB
ARISTA_INGRESS_BASE = "1.3.6.1.4.1.30065.3.6.1.1.1"
ARISTA_EGRESS_BASE = "1.3.6.1.4.1.30065.3.6.1.2.1"
# Datadog topology expects MAC addresses for chassis/port when subtype is macAddress (4/3)
# Generate deterministic MAC from IP: 172.20.0.x -> 00:16:20:00:00:xx
def ip_to_mac_hex(ip):
    parts = ip.split(".")
    return f"0016200000{int(parts[3]):02x}"
# CISCO-CDP-MIB: 1.3.6.1.4.1.9.9.23.1.2.1.1 (cdpCacheEntry)
# Index: ifIndex.deviceIndex (1.1 = first neighbor on ifIndex 1)
CDP_CACHE_BASE = "1.3.6.1.4.1.9.9.23.1.2.1.1"

# PAN-COMMON-MIB (Palo Alto) - session metrics
PAN_SESSION_UTIL = "1.3.6.1.4.1.25461.2.1.2.3.1.0"
PAN_SESSION_MAX = "1.3.6.1.4.1.25461.2.1.2.3.2.0"
PAN_SESSION_ACTIVE = "1.3.6.1.4.1.25461.2.1.2.3.3.0"

# IF-MIB ifHCInOctets (6), ifHCOutOctets (10) - tier-based throughput for data center flow
IF_HC_IN = "1.3.6.1.2.1.31.1.1.1.6"
IF_HC_OUT = "1.3.6.1.2.1.31.1.1.1.10"
# Throughput tiers (bytes): Edge highest, PDU lowest - reflects Internet→DC flow
THROUGHPUT_TIERS = {1: 120e9, 2: 90e9, 3: 70e9, 4: 55e9, 5: 25e9, 6: 12e9, 7: 2e9}

# Architecture: Internet→ASR→PA1/PA2→F5→Core1/Core2→Leaf/MDS/Catalyst→WLC/PDU
# Each link: local_port (this device) ↔ remote_port (neighbor). Order = port assignment.
DEVICES = {
    "cisco-asr1001": {
        "sysdescr": "Cisco IOS XE Software, Version 17.9.4, ASR1001-X (Cisco ASR1001-X)",
        "sysobjectid": ".1.3.6.1.4.1.9.1.1165",  # ciscoASR1001
        "sysname": "edge-router-asr1001",
        "ip": "172.20.0.10",
        "throughput_tier": 1,
        "cisco": True,
        "cpu_pct": 22,  # Edge router: 15-25% typical
        "memory_total_kb": 8388608,   # 8GB
        "memory_used_kb": 5242880,   # ~6GB used
        "lldp_neighbors": [
            {"name": "paloalto-pa3220-1", "sysname": "paloalto-pa3220-1", "desc": "Palo Alto PA-3220", "ip": "172.20.0.11", "local_port": "A1", "remote_port": "A1"},
            {"name": "paloalto-pa3220-2", "sysname": "paloalto-pa3220-2", "desc": "Palo Alto PA-3220", "ip": "172.20.0.12", "local_port": "A2", "remote_port": "A1"},
        ],
        "cdp_neighbors": [
            {
                "name": "paloalto-pa3220-1",
                "platform": "Palo Alto PA-3220",
                "ip": "172.20.0.11",
                "device_port": "GigabitEthernet0/1/0",
                "version": "PAN-OS 10.2.0",
            },
            {
                "name": "paloalto-pa3220-2",
                "platform": "Palo Alto PA-3220",
                "ip": "172.20.0.12",
                "device_port": "GigabitEthernet0/2/0",
                "version": "PAN-OS 10.2.0",
            },
        ],
    },
    "paloalto-pa3220-1": {
        "sysdescr": "Palo Alto Networks PA-3220 firewall, PAN-OS 10.2.0",
        "sysobjectid": ".1.3.6.1.4.1.25461.2.3.1",  # palo-alto (1.3.6.1.4.1.25461.2.3.*)
        "sysname": "paloalto-pa3220-1",
        "ip": "172.20.0.11",
        "throughput_tier": 2,
        "cisco": False,
        "cpu_pct": 28,  # Firewall: 25-35% typical
        "memory_total_kb": 16777216,  # 16GB
        "memory_used_kb": 10485760,   # ~10GB used
        "palo_alto": True,
        "pan_session_max": 1000000,
        "pan_session_active": 185000,
        "lldp_neighbors": [
            {"name": "cisco-asr1001", "sysname": "edge-router-asr1001", "desc": "Cisco ASR1001-X", "ip": "172.20.0.10", "local_port": "A1", "remote_port": "A1"},
            {"name": "f5-bigip-ltm", "sysname": "f5-bigip-ltm-dmz", "desc": "F5 BIG-IP LTM", "ip": "172.20.0.13", "local_port": "A2", "remote_port": "A1"},
        ],
    },
    "paloalto-pa3220-2": {
        "sysdescr": "Palo Alto Networks PA-3220 firewall, PAN-OS 10.2.0",
        "sysobjectid": ".1.3.6.1.4.1.25461.2.3.2",  # palo-alto
        "sysname": "paloalto-pa3220-2",
        "ip": "172.20.0.12",
        "throughput_tier": 2,
        "cisco": False,
        "cpu_pct": 26,
        "memory_total_kb": 16777216,
        "memory_used_kb": 9961472,   # ~9.5GB
        "palo_alto": True,
        "pan_session_max": 1000000,
        "pan_session_active": 142000,
        "lldp_neighbors": [
            {"name": "cisco-asr1001", "sysname": "edge-router-asr1001", "desc": "Cisco ASR1001-X", "ip": "172.20.0.10", "local_port": "A1", "remote_port": "A2"},
            {"name": "f5-bigip-ltm", "sysname": "f5-bigip-ltm-dmz", "desc": "F5 BIG-IP LTM", "ip": "172.20.0.13", "local_port": "A2", "remote_port": "A2"},
        ],
    },
    "f5-bigip-ltm": {
        "sysdescr": "F5 BIG-IP LTM, Version 16.1.3, Build 0.0.11",
        "sysobjectid": ".1.3.6.1.4.1.3375.2.1.3.4.1",  # f5-big-ip (1.3.6.1.4.1.3375.2.1.3.4.*)
        "sysname": "f5-bigip-ltm-dmz",
        "ip": "172.20.0.13",
        "throughput_tier": 3,
        "cisco": False,
        "cpu_pct": 18,  # Load balancer: 15-25% typical
        "memory_total_kb": 16777216,
        "memory_used_kb": 9437184,   # ~9GB
        "lldp_neighbors": [
            {"name": "paloalto-pa3220-1", "sysname": "paloalto-pa3220-1", "desc": "Palo Alto PA-3220", "ip": "172.20.0.11", "local_port": "A1", "remote_port": "A2"},
            {"name": "paloalto-pa3220-2", "sysname": "paloalto-pa3220-2", "desc": "Palo Alto PA-3220", "ip": "172.20.0.12", "local_port": "A2", "remote_port": "A2"},
            {"name": "arista-7280r-core1", "sysname": "arista-7280r-core1", "desc": "Arista 7280R", "ip": "172.20.0.14", "local_port": "A3", "remote_port": "A1"},
            {"name": "arista-7280r-core2", "sysname": "arista-7280r-core2", "desc": "Arista 7280R", "ip": "172.20.0.15", "local_port": "A4", "remote_port": "A1"},
        ],
    },
    "arista-7280r-core1": {
        "sysdescr": "Arista Networks EOS version 4.28.3F running on an Arista Networks DCS-7280SR-48C6",
        "sysobjectid": ".1.3.6.1.4.1.30065.1.3011.7280.1347.48.2878.6",  # matches arista-switch (LLDP)
        "sysname": "arista-7280r-core1",
        "ip": "172.20.0.14",
        "arista_model": "DCS-7280SR-48C6",
        "throughput_tier": 4,
        "cisco": False,
        "cpu_pct": 12,  # Core switch: 8-15% typical
        "memory_total_kb": 8388608,
        "memory_used_kb": 4194304,   # ~4GB
        "lldp_neighbors": [
            {"name": "f5-bigip-ltm", "sysname": "f5-bigip-ltm-dmz", "desc": "F5 BIG-IP LTM", "ip": "172.20.0.13", "local_port": "A1", "remote_port": "A3"},
            {"name": "arista-7280r-core2", "sysname": "arista-7280r-core2", "desc": "Arista 7280R MLAG", "ip": "172.20.0.15", "local_port": "A2", "remote_port": "A2"},
            {"name": "arista-7050x-leaf1", "sysname": "arista-7050x-leaf1", "desc": "Arista 7050X", "ip": "172.20.0.16", "local_port": "A3", "remote_port": "A1"},
            {"name": "cisco-mds-9148", "sysname": "cisco-mds-9148-san", "desc": "Cisco MDS 9148", "ip": "172.20.0.18", "local_port": "A4", "remote_port": "A1"},
            {"name": "cisco-catalyst-9300", "sysname": "cisco-catalyst-9300-access", "desc": "Cisco Catalyst 9300", "ip": "172.20.0.19", "local_port": "A5", "remote_port": "A1"},
        ],
    },
    "arista-7280r-core2": {
        "sysdescr": "Arista Networks EOS version 4.28.3F running on an Arista Networks DCS-7280SR-48C6",
        "sysobjectid": ".1.3.6.1.4.1.30065.1.3011.7280.1347.48.2878.6",  # matches arista-switch (LLDP)
        "sysname": "arista-7280r-core2",
        "ip": "172.20.0.15",
        "arista_model": "DCS-7280SR-48C6",
        "throughput_tier": 4,
        "cisco": False,
        "cpu_pct": 11,
        "memory_total_kb": 8388608,
        "memory_used_kb": 3984588,
        "lldp_neighbors": [
            {"name": "f5-bigip-ltm", "sysname": "f5-bigip-ltm-dmz", "desc": "F5 BIG-IP LTM", "ip": "172.20.0.13", "local_port": "A1", "remote_port": "A4"},
            {"name": "arista-7280r-core1", "sysname": "arista-7280r-core1", "desc": "Arista 7280R MLAG", "ip": "172.20.0.14", "local_port": "A2", "remote_port": "A2"},
            {"name": "arista-7050x-leaf2", "sysname": "arista-7050x-leaf2", "desc": "Arista 7050X", "ip": "172.20.0.17", "local_port": "A3", "remote_port": "A1"},
            {"name": "cisco-mds-9148", "sysname": "cisco-mds-9148-san", "desc": "Cisco MDS 9148", "ip": "172.20.0.18", "local_port": "A4", "remote_port": "A2"},
            {"name": "cisco-catalyst-9300", "sysname": "cisco-catalyst-9300-access", "desc": "Cisco Catalyst 9300", "ip": "172.20.0.19", "local_port": "A5", "remote_port": "A2"},
        ],
    },
    "arista-7050x-leaf1": {
        "sysdescr": "Arista Networks EOS version 4.28.3F running on an Arista Networks DCS-7050X-48",
        "sysobjectid": ".1.3.6.1.4.1.30065.1.3011.7050.1958.128",  # matches arista-switch (LLDP)
        "sysname": "arista-7050x-leaf1",
        "ip": "172.20.0.16",
        "arista_model": "DCS-7050X-48",
        "throughput_tier": 5,
        "cisco": False,
        "cpu_pct": 8,   # Leaf switch: 5-12% typical
        "memory_total_kb": 4194304,
        "memory_used_kb": 2097152,
        "lldp_neighbors": [
            {"name": "arista-7280r-core1", "sysname": "arista-7280r-core1", "desc": "Arista 7280R", "ip": "172.20.0.14", "local_port": "A1", "remote_port": "A3"},
        ],
    },
    "arista-7050x-leaf2": {
        "sysdescr": "Arista Networks EOS version 4.28.3F running on an Arista Networks DCS-7050X-48",
        "sysobjectid": ".1.3.6.1.4.1.30065.1.3011.7050.1958.128",  # matches arista-switch (LLDP)
        "sysname": "arista-7050x-leaf2",
        "ip": "172.20.0.17",
        "arista_model": "DCS-7050X-48",
        "throughput_tier": 5,
        "cisco": False,
        "cpu_pct": 7,
        "memory_total_kb": 4194304,
        "memory_used_kb": 1887436,
        "lldp_neighbors": [
            {"name": "arista-7280r-core2", "sysname": "arista-7280r-core2", "desc": "Arista 7280R", "ip": "172.20.0.15", "local_port": "A1", "remote_port": "A3"},
        ],
    },
    "cisco-mds-9148": {
        "sysdescr": "Cisco MDS 9148S 16G 48-Port Fabric Switch, NX-OS 9.3(1)",
        # CISCO-PRODUCTS-MIB: MDS 9000 / NX-OS SAN family (not a Nexus 7K switch OID)
        "sysobjectid": ".1.3.6.1.4.1.9.1.1737",  # ciscoMds9848512K9SM — MDS 9000 line; lab analogue for MDS 9148S
        "sysname": "cisco-mds-9148-san",
        "ip": "172.20.0.18",
        "throughput_tier": 6,
        "cisco": True,
        "cpu_pct": 4,   # SAN switch: 5-10% typical
        "memory_total_kb": 4194304,
        "memory_used_kb": 1572864,   # ~1.5GB
        "lldp_neighbors": [
            {"name": "arista-7280r-core1", "sysname": "arista-7280r-core1", "desc": "Arista 7280R", "ip": "172.20.0.14", "local_port": "A1", "remote_port": "A4"},
            {"name": "arista-7280r-core2", "sysname": "arista-7280r-core2", "desc": "Arista 7280R", "ip": "172.20.0.15", "local_port": "A2", "remote_port": "A4"},
        ],
        "cdp_neighbors": [
            {
                "name": "arista-7280r-core1",
                "platform": "Arista Networks DCS-7280",
                "ip": "172.20.0.14",
                "device_port": "fc1/1",
                "version": "Arista EOS 4.28.3F",
            },
            {
                "name": "arista-7280r-core2",
                "platform": "Arista Networks DCS-7280",
                "ip": "172.20.0.15",
                "device_port": "fc1/2",
                "version": "Arista EOS 4.28.3F",
            },
        ],
    },
    "cisco-catalyst-9300": {
        "sysdescr": "Cisco IOS-XE Software, Catalyst 9300 48-Port, Version 17.9.4",
        "sysobjectid": ".1.3.6.1.4.1.9.1.2802",  # cisco-catalyst (ciscoCat9300L24UXG2Q)
        "sysname": "cisco-catalyst-9300-access",
        "chassis_serial": "FCW2308L0CA",
        "ip": "172.20.0.19",
        "throughput_tier": 5,
        "cisco": True,
        "cpu_pct": 10,  # Access switch: 5-15% typical
        "memory_total_kb": 8388608,
        "memory_used_kb": 3145728,   # ~3GB
        "lldp_neighbors": [
            {"name": "arista-7280r-core1", "sysname": "arista-7280r-core1", "desc": "Arista 7280R", "ip": "172.20.0.14", "local_port": "A1", "remote_port": "A5"},
            {"name": "arista-7280r-core2", "sysname": "arista-7280r-core2", "desc": "Arista 7280R", "ip": "172.20.0.15", "local_port": "A2", "remote_port": "A5"},
            {"name": "cisco-9800-wlc", "sysname": "cisco-9800-wlc", "desc": "Cisco 9800 WLC", "ip": "172.20.0.20", "local_port": "A3", "remote_port": "A1"},
            {"name": "apc-ap8853-pdu", "sysname": "apc-ap8853-pdu", "desc": "APC AP8853 PDU", "ip": "172.20.0.21", "local_port": "A4", "remote_port": "A1"},
        ],
        "cdp_neighbors": [
            {
                "name": "cisco-9800-wlc",
                "platform": "Cisco Catalyst 9800-CL Wireless Controller",
                "ip": "172.20.0.20",
                "device_port": "GigabitEthernet1/0/1",
                "version": "Cisco IOS-XE 17.9.4",
            },
        ],
    },
    "cisco-9800-wlc": {
        "sysdescr": "Cisco IOS XE Software, Catalyst 9800-CL Wireless Controller, Version 17.9.4",
        "sysobjectid": ".1.3.6.1.4.1.9.1.2391",  # cisco-catalyst-wlc (ciscoC9800CLK9)
        "sysname": "cisco-9800-wlc",
        "ip": "172.20.0.20",
        "throughput_tier": 6,
        "cisco": True,
        "cpu_pct": 25,  # WLC: 20-30% typical
        "memory_total_kb": 8388608,
        "memory_used_kb": 5242880,   # ~5GB
        "lldp_neighbors": [
            {"name": "cisco-catalyst-9300", "sysname": "cisco-catalyst-9300-access", "desc": "Cisco Catalyst 9300", "ip": "172.20.0.19", "local_port": "A1", "remote_port": "A3"},
        ],
        "cdp_neighbors": [
            {
                "name": "cisco-catalyst-9300",
                "platform": "Cisco Catalyst 9300",
                "ip": "172.20.0.19",
                "device_port": "GigabitEthernet1/0/3",
                "version": "Cisco IOS-XE 17.9.4",
            },
        ],
    },
    "apc-ap8853-pdu": {
        "sysdescr": "APC AP8853, Rack PDU, 3 Phase, Firmware 6.9.4",
        "sysobjectid": ".1.3.6.1.4.1.318.1.3.4.1",  # apc-pdu (1.3.6.1.4.1.318.1.3.4.*)
        "sysname": "apc-ap8853-pdu",
        "ip": "172.20.0.21",
        "throughput_tier": 7,
        "cisco": False,
        "cpu_pct": 2,   # PDU: minimal
        "memory_total_kb": 524288,   # 512MB
        "memory_used_kb": 204800,    # ~200MB
        "lldp_neighbors": [
            {"name": "cisco-catalyst-9300", "sysname": "cisco-catalyst-9300-access", "desc": "Cisco Catalyst 9300", "ip": "172.20.0.19", "local_port": "A1", "remote_port": "A4"},
        ],
    },
}

BASE_FILE = "data/mocksnmp.snmprec"


def _port_num(port_str):
    """Extract port number from A1, A2, etc."""
    return int(port_str.replace("A", "")) if isinstance(port_str, str) else port_str


def lldp_loc_port_entries(neighbors):
    """Generate lldpLocPortTable entries so agent can map LocalPortNum to interface.
    Ports are from local_port on each neighbor (A1, A2, ...) for direct interface-to-interface links."""
    if not neighbors:
        return []
    max_port = max(_port_num(n.get("local_port", f"A{i}")) for i, n in enumerate(neighbors, 1))
    lines = []
    for port in range(1, max_port + 1):
        if_name = f"A{port}"  # matches IF-MIB ifName for ifIndex
        lines.append(f"{LLDP_LOC_PORT_BASE}.1.{port}|2|{port}")
        lines.append(f"{LLDP_LOC_PORT_BASE}.2.{port}|2|5")
        lines.append(f"{LLDP_LOC_PORT_BASE}.3.{port}|4|{if_name}")
        lines.append(f"{LLDP_LOC_PORT_BASE}.4.{port}|4|Ethernet{port}")
    return lines


def lldp_entries(neighbors):
    """Generate snmprec lines for lldpRemTable entries.
    Each neighbor on its local_port (A1, A2, ...) for direct interface-to-interface topology links.
    lldpRemPortId = remote device's interface for bidirectional link correlation."""
    lines = []
    lines.append(f"1.0.8802.1.1.2.1.2.4.0|2|{len(neighbors)}")
    for n in neighbors:
        port_num = _port_num(n.get("local_port", "A1"))
        idx = f"0.{port_num}.1"
        mac_hex = ip_to_mac_hex(n.get("ip", "172.20.0.1"))
        remote_port = n.get("remote_port", "A1")
        lines.append(f"{LLDP_REM_BASE}.4.{idx}|2|4")
        lines.append(f"{LLDP_REM_BASE}.5.{idx}|4x|{mac_hex}")
        lines.append(f"{LLDP_REM_BASE}.6.{idx}|2|5")
        lines.append(f"{LLDP_REM_BASE}.7.{idx}|4|{remote_port}")
        lines.append(f"{LLDP_REM_BASE}.9.{idx}|4|{n.get('sysname', n['name'])}")
        lines.append(f"{LLDP_REM_BASE}.10.{idx}|4|{n['desc']}")
    return lines


# HOST-RESOURCES-MIB for CPU and memory (Datadog _generic-host-resources)
# hrProcessorTable: 1.3.6.1.2.1.25.3.3.1.2 = hrProcessorLoad (cpu.usage)
# hrStorageTable: 1.3.6.1.2.1.25.2.3.1.5 = hrStorageSize, 1.3.6.1.2.1.25.2.3.1.6 = hrStorageUsed
def host_resources_entries(device_values):
    """Generate HOST-RESOURCES-MIB entries with device-specific CPU/memory values."""
    cpu = device_values.get("cpu_pct", 20)
    total_kb = device_values.get("memory_total_kb", 8388608)
    used_kb = device_values.get("memory_used_kb", 4194304)
    used_kb = min(used_kb, total_kb)
    cpu = max(0, min(100, int(cpu)))
    lines = []
    lines.append(f"1.3.6.1.2.1.25.3.3.1.2.1|2|{cpu}")
    lines.append("1.3.6.1.2.1.25.2.3.1.1.1|2|1")
    lines.append("1.3.6.1.2.1.25.2.3.1.2.1|6|.1.3.6.1.2.1.25.2.1.2")
    lines.append("1.3.6.1.2.1.25.2.3.1.3.1|4|Physical memory")
    lines.append("1.3.6.1.2.1.25.2.3.1.4.1|2|1024")
    lines.append(f"1.3.6.1.2.1.25.2.3.1.5.1|2|{total_kb}")
    lines.append(f"1.3.6.1.2.1.25.2.3.1.6.1|2|{used_kb}")
    return lines


def palo_alto_entries(device_values):
    """PAN-COMMON-MIB session metrics for Palo Alto firewalls."""
    max_sess = device_values.get("pan_session_max", 1000000)
    active = device_values.get("pan_session_active", 150000)
    max_sess = max(max_sess, 1)
    # Session table % should track active vs max (avoids contradictory util vs active)
    util = device_values.get("pan_session_util")
    if util is None:
        util = min(100, max(0, int(round(100.0 * active / max_sess))))
    else:
        util = max(0, min(100, int(util)))
    return [
        f"{PAN_SESSION_UTIL}|2|{util}",
        f"{PAN_SESSION_MAX}|2|{max_sess}",
        f"{PAN_SESSION_ACTIVE}|2|{active}",
    ]


# CISCO-STACK-MIB - chassisSerialNumberString (required by cisco-catalyst profile metadata)
CISCO_CHASSIS_SERIAL = "1.3.6.1.4.1.9.5.1.2.19.0"


def cisco_catalyst_entries(device_values):
    """Cisco Catalyst profile: CISCO-STACK-MIB chassisSerialNumberString for metadata."""
    serial = device_values.get("chassis_serial", "FCW2308L0CA")
    return [f"{CISCO_CHASSIS_SERIAL}|4|{serial}"]


def cdp_entries(neighbors):
    """Generate snmprec lines for cdpCacheTable entries."""
    lines = []
    for i, n in enumerate(neighbors, 1):
        idx = f"1.{i}"  # ifIndex=1, deviceIndex=i
        ip = n.get("ip", "0.0.0.0")
        device_port = n.get("device_port", "GigabitEthernet1/0/1")
        version = n.get("version", "Unknown")
        # cdpCacheAddressType (1=ipv4)
        lines.append(f"{CDP_CACHE_BASE}.3.{idx}|2|1")
        # cdpCacheAddress (IPv4 dotted decimal)
        lines.append(f"{CDP_CACHE_BASE}.4.{idx}|4|{ip}")
        # cdpCacheVersion (neighbor software — not always IOS on the remote)
        lines.append(f"{CDP_CACHE_BASE}.5.{idx}|4|{version}")
        # cdpCacheDeviceId
        lines.append(f"{CDP_CACHE_BASE}.6.{idx}|4|{n['name']}")
        # cdpCacheDevicePort (remote port toward us)
        lines.append(f"{CDP_CACHE_BASE}.7.{idx}|4|{device_port}")
        # cdpCachePlatform
        lines.append(f"{CDP_CACHE_BASE}.8.{idx}|4|{n['platform']}")
    return lines


def arista_entries(device_values, num_lldp_ports):
    """Arista profile MIBs: ENTITY-SENSOR-MIB, ARISTA-QUEUE-MIB.
    ENTITY-MIB index 1 is replaced in main loop. Covers all profile metrics for topology interfaces."""
    lines = []
    # ENTITY-SENSOR-MIB - temp (8=celsius), power (6=watts), operStatus (1=ok)
    # Avoid 0 W readings with operStatus=ok (use minimal plausible draw for PSU sensors)
    for idx, sens_type, value in [(25, 8, 42), (26, 8, 38), (30, 6, 450), (31, 6, 448), (32, 6, 12)]:
        lines.append(f"{ENT_PHY_SENSOR_BASE}.1.{idx}|2|{sens_type}")
        lines.append(f"{ENT_PHY_SENSOR_BASE}.4.{idx}|2|{value}")
        lines.append(f"{ENT_PHY_SENSOR_BASE}.5.{idx}|2|1")
    # ARISTA-QUEUE-MIB - ingress/egress queue stats per interface (1..num_lldp_ports)
    for if_idx in range(1, num_lldp_ports + 1):
        for q_idx in range(8):
            lines.append(f"{ARISTA_INGRESS_BASE}.1.{if_idx}.{q_idx}|2|{if_idx}")
            lines.append(f"{ARISTA_INGRESS_BASE}.2.{if_idx}.{q_idx}|2|{q_idx}")
            lines.append(f"{ARISTA_INGRESS_BASE}.3.{if_idx}.{q_idx}|2|{q_idx * 100}")
            lines.append(f"{ARISTA_EGRESS_BASE}.1.{if_idx}.{q_idx}|2|{if_idx}")
            lines.append(f"{ARISTA_EGRESS_BASE}.2.{if_idx}.{q_idx}|2|{q_idx}")
            lines.append(f"{ARISTA_EGRESS_BASE}.6.{if_idx}.{q_idx}|2|{q_idx * 50}")
    return lines


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.join(script_dir, BASE_FILE)

    with open(base_path) as f:
        base_content = f.read()

    for device, values in DEVICES.items():
        out_dir = os.path.join(script_dir, "data", device)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "mocksnmp.snmprec")

        lines = base_content.split("\n")
        new_lines = []
        is_arista = device.startswith("arista-")
        lldp_neighbors = values.get("lldp_neighbors", [])
        tier = values.get("throughput_tier", 5)
        base_bytes = int(THROUGHPUT_TIERS.get(tier, 25e9))
        for line in lines:
            if line.startswith("1.3.6.1.2.1.1.1.0|"):
                new_lines.append(f"1.3.6.1.2.1.1.1.0|4|{values['sysdescr']}")
            elif line.startswith("1.3.6.1.2.1.1.2.0|"):
                new_lines.append(f"1.3.6.1.2.1.1.2.0|6|{values['sysobjectid']}")
            elif line.startswith("1.3.6.1.2.1.1.5.0|"):
                new_lines.append(f"1.3.6.1.2.1.1.5.0|4|{values['sysname']}")
            elif line.startswith("1.3.6.1.2.1.1.3.0|"):
                # RFC 1213 sysUpTime is TimeTicks (snmpsim tag 67), not OctetString
                tick = 3_600_000 + 50_000 * int(values["ip"].rsplit(".", 1)[-1])
                new_lines.append(f"1.3.6.1.2.1.1.3.0|67|{tick}")
            elif line.startswith("1.3.6.1.2.1.1.4.0|"):
                new_lines.append("1.3.6.1.2.1.1.4.0|4|snmp-lab@example.com")
            elif line.startswith("1.3.6.1.2.1.1.6.0|"):
                new_lines.append("1.3.6.1.2.1.1.6.0|4|DC-Lab / SNMP sandbox")
            elif is_arista and line.startswith("1.3.6.1.2.1.47.1.1.1.1.2.1|"):
                new_lines.append(f"{ENTITY_PHYS_BASE}.2.1|4|{values.get('arista_model', 'DCS-7280SR-48C6')} Chassis")
            elif is_arista and line.startswith("1.3.6.1.2.1.47.1.1.1.1.8.1|"):
                new_lines.append(f"{ENTITY_PHYS_BASE}.8.1|4|12.00")
            elif is_arista and line.startswith("1.3.6.1.2.1.47.1.1.1.1.11.1|"):
                serial = f"JSN{values.get('sysname', 'arista')[:8].upper().replace('-', '')}001"
                new_lines.append(f"{ENTITY_PHYS_BASE}.11.1|4|{serial}")
            elif is_arista and line.startswith("1.3.6.1.2.1.47.1.1.1.1.13.1|"):
                new_lines.append(f"{ENTITY_PHYS_BASE}.13.1|4|{values.get('arista_model', 'DCS-7280SR-48C6')}")
            else:
                # Tier-based throughput for topology interfaces (data center flow)
                replaced = False
                num_ports = max(_port_num(n.get("local_port", f"A{i}")) for i, n in enumerate(lldp_neighbors, 1)) if lldp_neighbors else 1
                for i in range(1, num_ports + 1):
                    in_oid, out_oid = f"{IF_HC_IN}.{i}|", f"{IF_HC_OUT}.{i}|"
                    in32, out32 = f"1.3.6.1.2.1.2.2.1.10.{i}|", f"1.3.6.1.2.1.2.2.1.16.{i}|"
                    hc_in = int(base_bytes * (1 - 0.05 * i))
                    hc_out = int(base_bytes * 0.9 * (1 - 0.05 * i))
                    if line.startswith(in_oid):
                        new_lines.append(f"{IF_HC_IN}.{i}|70|{hc_in}")
                        replaced = True
                        break
                    if line.startswith(out_oid):
                        new_lines.append(f"{IF_HC_OUT}.{i}|70|{hc_out}")
                        replaced = True
                        break
                    # IF-MIB: keep 32-bit counters in range and ≤ HC for high-speed interfaces
                    if line.startswith(in32):
                        new_lines.append(f"1.3.6.1.2.1.2.2.1.10.{i}|65|{min(hc_in, 2**32 - 1)}")
                        replaced = True
                        break
                    if line.startswith(out32):
                        new_lines.append(f"1.3.6.1.2.1.2.2.1.16.{i}|65|{min(hc_out, 2**32 - 1)}")
                        replaced = True
                        break
                if not replaced:
                    new_lines.append(line)

        # Append HOST-RESOURCES-MIB (CPU, memory) with device-specific values
        new_lines.append("")
        new_lines.append("# HOST-RESOURCES-MIB - CPU and memory")
        new_lines.extend(host_resources_entries(values))

        # Append Palo Alto session metrics (firewalls only)
        if values.get("palo_alto"):
            new_lines.append("")
            new_lines.append("# PAN-COMMON-MIB - session utilization")
            new_lines.extend(palo_alto_entries(values))

        # Append LLDP data (all devices)
        if lldp_neighbors:
            new_lines.append("")
            new_lines.append("# LLDP-MIB - lldpLocPortTable (port→interface for topology)")
            new_lines.extend(lldp_loc_port_entries(lldp_neighbors))
            new_lines.append("")
            new_lines.append("# LLDP-MIB - neighbor discovery (one neighbor per port)")
            new_lines.extend(lldp_entries(lldp_neighbors))

        # Append Arista profile MIBs (sensors, queue stats for topology interfaces)
        if device.startswith("arista-") and lldp_neighbors:
            new_lines.append("")
            new_lines.append("# ENTITY-SENSOR-MIB, ARISTA-QUEUE-MIB - Arista profile completeness")
            max_port = max(_port_num(n.get("local_port", f"A{i}")) for i, n in enumerate(lldp_neighbors, 1))
            new_lines.extend(arista_entries(values, max_port))

        # Append CDP data (Cisco devices only)
        if values.get("cisco") and values.get("cdp_neighbors"):
            new_lines.append("")
            new_lines.append("# CISCO-CDP-MIB - Cisco neighbor discovery")
            new_lines.extend(cdp_entries(values["cdp_neighbors"]))

        # Append Cisco Catalyst profile (CISCO-STACK-MIB chassisSerialNumberString)
        if device == "cisco-catalyst-9300":
            new_lines.append("")
            new_lines.append("# CISCO-STACK-MIB - cisco-catalyst profile metadata")
            new_lines.extend(cisco_catalyst_entries(values))

        # snmpsim requires snmprec files sorted by OID for getnext/snmpwalk to work
        data_lines = [l for l in new_lines if "|" in l and not l.strip().startswith("#")]
        comment_lines = [l for l in new_lines if "|" not in l or l.strip().startswith("#")]
        def oid_key(line):
            oid = line.split("|", 1)[0].strip()
            return tuple(int(x) if x.isdigit() else 0 for x in oid.split("."))
        data_lines.sort(key=oid_key)
        new_lines = data_lines + comment_lines

        with open(out_path, "w") as f:
            f.write("\n".join(new_lines))
        print(f"Created {out_path} (LLDP: {len(lldp_neighbors)} neighbors" +
              (f", CDP: {len(values['cdp_neighbors'])} neighbors" if values.get("cdp_neighbors") else "") + ")")

    print(
        "\nSNMP data is baked into the simulator Docker image. After edits, rebuild locally: "
        "cd snmp && SNMP_SIM_IMAGE=snmp_container:local docker compose build cisco-asr1001 && docker compose up -d"
        "  (then ./publish-dockerhub.sh to push matthewruyffelaert667/snmp-sandbox-sim if you publish)."
    )


if __name__ == "__main__":
    main()
