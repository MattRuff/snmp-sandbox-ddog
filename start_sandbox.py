#!/usr/bin/env python3
import os
import sys
import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

BRed = '\033[1;31m'
BGreen = '\033[1;32m'
NC = '\033[0m'  # No Color


def _dd_api_key_configured():
    if os.environ.get("DD_API_KEY", "").strip():
        return True
    env_path = os.path.join(SCRIPT_DIR, "snmp", ".env")
    if not os.path.isfile(env_path):
        return False
    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("DD_API_KEY="):
                    return bool(line[len("DD_API_KEY=") :].strip().strip("'\""))
    except OSError:
        pass
    return False


if not _dd_api_key_configured():
    print(
        f"{BRed}DD_API_KEY is not set. Export it or add it to snmp/.env (copy from snmp/.env.example). "
        f"Never commit API keys.{NC}"
    )
    sys.exit(1)

os.makedirs('tcpdump', exist_ok=True)

os.chdir('snmp')

print(f"{BGreen}################# Building docker image and Datadog Agent ##############################{NC}")

# Build and start SNMP containers + Datadog Agent (agent is in docker-compose)
os.system('docker compose up --build --force-recreate -d')

print(f"{BRed}\nDocker up (SNMP devices + datadog-agent){NC}")

print(f"{BGreen}\n################## TCPDUMP started, please wait 30 seconds "
      f"#######################################\n{BRed}")

timestamp = datetime.datetime.now().strftime('%m-%d-%Y')

# Starting a tcpdump filtering traffic on port 161 to closer inspect
os.system(f'docker exec datadog-agent tcpdump -T snmp -c 30 '
          f'-w /tcpdumps/dump{timestamp}.pcap')

tcpdump_path = os.path.join(SCRIPT_DIR, 'tcpdump', f'dump{timestamp}.pcap')
print(f"{NC}\nWriting output of check to {tcpdump_path}")

#print(f"{BGreen}\nRunning comparison of OID's configured in profile to OID in snmprec{NC}")
#print(f"{BRed}\nThe following OID's in your snmp profile were configured\n{NC}")
os.chdir('..')
#os.system('python3 compare.py')

print(f"{BGreen}\n################### Running SNMP check ####################################{NC}")
print(f"{BRed}\nWriting output of check to {os.path.join(SCRIPT_DIR, 'tcpdump', 'debug_snmp_check.log')}{NC}")
os.chdir('snmp')

# Run DEBUG level SNMP check, out put to file locally
os.system("docker exec datadog-agent bash -c 'agent check snmp -l debug > /tcpdumps/debug_snmp_check.log'")

print(f"{BGreen}\nDo you want to open the .pcap file in Wireshark now? (y|n){NC}?")
read_answer = input().lower()
if read_answer in ('yes', 'y'):
    system_name = os.uname().sysname
    pcap_path = os.path.join(SCRIPT_DIR, 'tcpdump', f'dump{timestamp}.pcap')

    if system_name == 'Darwin':
        # Mac branch
        if os.path.isdir('/Applications/Wireshark.app'):
            os.system(f'open -n -a /Applications/Wireshark.app "{pcap_path}"')
        else:
            os.system('brew install wireshark')
            os.system(f'open -n -a /Applications/Wireshark.app "{pcap_path}"')
    elif system_name.startswith('Linux'):
        # Linux branch
        if os.path.isdir('/etc/wireshark'):
            os.system(f'wireshark "{pcap_path}"')
        else:
            os.system('sudo apt install wireshark -y')
            os.system(f'wireshark "{pcap_path}"')
else:
    print(f"{BGreen}Skipping Wireshark{NC}")

