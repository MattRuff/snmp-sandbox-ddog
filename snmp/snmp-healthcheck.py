#!/usr/bin/env python3
"""SNMP GET sysDescr on localhost:161 — confirms snmpsim answers v2c with community mocksnmp."""
import asyncio
import sys


async def check() -> int:
    from pysnmp.hlapi.asyncio import (
        CommunityData,
        ContextData,
        ObjectIdentity,
        ObjectType,
        SnmpEngine,
        UdpTransportTarget,
        getCmd,
    )

    snmp_engine = SnmpEngine()
    err_ind, err_stat, err_idx, varbinds = await getCmd(
        snmp_engine,
        CommunityData("mocksnmp", mpModel=1),
        UdpTransportTarget(("127.0.0.1", 161), timeout=2, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity("1.3.6.1.2.1.1.1.0")),
    )
    if err_ind:
        print(err_ind, file=sys.stderr)
        return 1
    if err_stat and int(err_stat) != 0:
        print(f"SNMP errorStatus={err_stat} index={err_idx}", file=sys.stderr)
        return 1
    for _oid, val in varbinds:
        if val is None or not str(val).strip():
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(check()))
