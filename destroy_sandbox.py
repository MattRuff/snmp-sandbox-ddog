import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(SCRIPT_DIR, "snmp"))

# Stop and remove all containers (SNMP devices + datadog-agent)
os.system("docker compose down --remove-orphans")

os.chdir(SCRIPT_DIR)

# Clear tcpdump output (keep dir)
os.makedirs("tcpdump", exist_ok=True)
os.system("rm -rf tcpdump/* 2>/dev/null || true")
