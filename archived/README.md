# Archived Components

These files were moved during sandbox cleanup. They are kept for reference but are no longer part of the active workflow.

## Contents

| Item | Reason archived |
|------|-----------------|
| **install_agent.py** | Datadog Agent is now in `snmp/docker-compose.yaml` and starts with SNMP containers |
| **parse_conf.py** | Disabled; docker-compose has fixed per-device services |
| **datadog.yaml** | Replaced by `agent_config/datadog-docker.yaml` (used by compose) |
| **references/datadog-agent-compose.yaml** | Standalone agent compose; agent now in main compose |
| **references/snmp_container-original.md** | Original reference doc |
| **conversion/** | Snmpwalk-to-snmprec converter; device data now from `generate_device_data.py` |
| **snmp_data_legacy/** | Old device folders (arista-7050x, arista-7280r, paloalto-pa3220) superseded by leaf1/leaf2, core1/core2, pa3220-1/pa3220-2 |

## Restoring

If you need any of these:

- **install_agent.py**: Use `snmp/docker-compose.yaml` datadog-agent service instead
- **conversion**: Run from `archived/conversion`; outputs to `snmp/data/mocksnmp.snmprec` (base file for generate_device_data)
