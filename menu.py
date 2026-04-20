import subprocess
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# Function to print colored text to the console
def print_color(text, color):
    print(f"\033[1;{color}m{text}\033[0m")

def convert_snmpwalk():
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], cwd=SCRIPT_DIR, check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=SCRIPT_DIR, check=True)
    subprocess.run(
        [sys.executable, "convert.py"],
        cwd=os.path.join(SCRIPT_DIR, "archived", "conversion"),
        check=True,
    )
    print_color("\nsnmpwalk converted successfully!", "32")


def start_containers():
    subprocess.run([sys.executable, "start_sandbox.py"], cwd=SCRIPT_DIR, check=True)
    print_color("Containers started successfully!", "32")


def destroy_containers():
    # Stop and remove containers using docker-compose
    subprocess.run([sys.executable, "destroy_sandbox.py"], cwd=SCRIPT_DIR, check=True)

    print_color("Venv and containers destroyed successfully!", "31")


def compare_oid():
    subprocess.run([sys.executable, "extract_oid.py"], cwd=SCRIPT_DIR, check=True)


def regenerate_device_data():
    """Regenerate per-device SNMP data (topology, throughput, Arista MIBs)."""
    subprocess.run(
        [sys.executable, "generate_device_data.py"],
        cwd=os.path.join(SCRIPT_DIR, "snmp"),
        check=True,
    )
    print_color("Device data regenerated. Restart containers to pick up changes.", "32")


# Main loop
while True:
    print_color("##########################################################################################", "31")
    print_color("\nWelcome to SNMP sandbox!", "32")
    print("\nPlease select an option:\n")
    print_color("1) Convert snmpwalk (archived/conversion)", "32")
    print_color("2) Start stack (compose.sandbox.yaml — same as: docker compose ... run sandbox-cli)", "32")
    print_color("3) Stop stack + clear tcpdump files", "31")
    print_color("4) Compare OID in profile to snmprec (pass profile path as arg)", "33")
    print_color("5) Regenerate device data (topology, throughput, Arista MIBs)", "32")
    print_color("6) Exit menu", "32")

    choice = input("\nEnter an option number (1-6): ")

    if choice == "1":
        convert_snmpwalk()
    elif choice == "2":
        start_containers()
    elif choice == "3":
        destroy_containers()
        break
    elif choice == "4":
        profile = input("Profile YAML path (or Enter to skip): ").strip()
        if profile:
            subprocess.run([sys.executable, "extract_oid.py", profile], cwd=SCRIPT_DIR, check=True)
        else:
            print_color(f"Usage: {sys.executable} extract_oid.py <path/to/profile.yaml>", "33")
    elif choice == "5":
        regenerate_device_data()
    elif choice == "6":
        print_color("Exited menu", "31")
        break
    else:
        print_color("Invalid choice. Please enter a valid option number.", "31")
