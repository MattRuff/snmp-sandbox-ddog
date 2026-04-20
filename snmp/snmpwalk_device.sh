#!/bin/bash
# Run snmpwalk against a device - uses container network for reliable connectivity
# Usage: ./snmpwalk_device.sh <device_ip|port|name> [oid]
# Examples:
#   ./snmpwalk_device.sh 172.20.0.10 system
#   ./snmpwalk_device.sh 11610 system
#   ./snmpwalk_device.sh cisco-asr1001 system

set -e
COMMUNITY="${SNMP_COMMUNITY:-mocksnmp}"
TARGET="$1"
OID="${2:-1.3.6.1.2.1.1}"

resolve_ip() {
  case "$1" in
    11610) echo 172.20.0.10 ;;
    11611) echo 172.20.0.11 ;;
    11612) echo 172.20.0.12 ;;
    11613) echo 172.20.0.13 ;;
    11614) echo 172.20.0.14 ;;
    11615) echo 172.20.0.15 ;;
    11616) echo 172.20.0.16 ;;
    11617) echo 172.20.0.17 ;;
    11618) echo 172.20.0.18 ;;
    11619) echo 172.20.0.19 ;;
    11620) echo 172.20.0.20 ;;
    11621) echo 172.20.0.21 ;;
    cisco-asr1001) echo 172.20.0.10 ;;
    paloalto-pa3220-1) echo 172.20.0.11 ;;
    paloalto-pa3220-2) echo 172.20.0.12 ;;
    f5-bigip-ltm) echo 172.20.0.13 ;;
    arista-7280r-core1) echo 172.20.0.14 ;;
    arista-7280r-core2) echo 172.20.0.15 ;;
    arista-7050x-leaf1) echo 172.20.0.16 ;;
    arista-7050x-leaf2) echo 172.20.0.17 ;;
    cisco-mds-9148) echo 172.20.0.18 ;;
    cisco-catalyst-9300) echo 172.20.0.19 ;;
    cisco-9800-wlc) echo 172.20.0.20 ;;
    apc-ap8853-pdu) echo 172.20.0.21 ;;
    *) echo "$1" ;;
  esac
}

if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 <device_ip|port|name> [oid]"
  echo ""
  echo "Devices: cisco-asr1001, paloalto-pa3220-1, paloalto-pa3220-2, f5-bigip-ltm,"
  echo "         arista-7280r-core1, arista-7280r-core2, arista-7050x-leaf1, arista-7050x-leaf2,"
  echo "         cisco-mds-9148, cisco-catalyst-9300, cisco-9800-wlc, apc-ap8853-pdu"
  exit 1
fi

IP=$(resolve_ip "$TARGET")
docker run --rm --network snmp_static-network ubuntu:22.04 bash -c \
  "apt-get update -qq && apt-get install -y -qq snmp > /dev/null && snmpwalk -v2c -c $COMMUNITY -t 5 $IP:161 $OID"
