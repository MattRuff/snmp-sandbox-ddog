def extract_oid_values(file_path):
    oid_values = []
    with open(file_path, 'r') as file:
        for line in file:
            if 'OID:' in line:
                oid_value = line.split('OID:')[1].strip()
                oid_values.append(oid_value)
    return oid_values

def check_oid_presence(file_path, oid_values):
    present_oids = []
    with open(file_path, 'r') as file:
        file_contents = file.read()
        for oid_value in oid_values:
            if oid_value not in file_contents:
                present_oids.append(oid_value)
    return present_oids

# dd_config_files removed - using generic autodiscovery. Pass profile YAML path as arg to check OIDs.
import os
import sys
config_file_path = sys.argv[1] if len(sys.argv) > 1 else None
oid_values = extract_oid_values(config_file_path) if config_file_path and os.path.exists(config_file_path) else []

# Read the file to check presence
presence_file_path = './snmp/data/mocksnmp.snmprec'

# Check for presence of OID values
present_oids = check_oid_presence(presence_file_path, oid_values)

def print_color(text, color):
    print(f"\033[1;{color}m{text}\033[0m", end="")

# Print the present OID values
for oid_value in present_oids:
    print_color("The following OID was present in your test profile but not your snmpwalk output: ", 31)
    print(oid_value)

