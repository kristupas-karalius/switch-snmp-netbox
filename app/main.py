import requests
import os
from datetime import datetime

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--dry-run", action="store_true", help="Dry-run mode")
args = parser.parse_args()
DRY_RUN = args.dry_run



# --- Config ---
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN")
NETBOX_URL = os.getenv("NETBOX_URL")

headers = {
    "Authorization": f"Token {NETBOX_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# --- Load SNMP output grouped by IP ---
def parse_snmp_output(file_path):
    snmp_data = {}
    current_ip = None

    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Detect a new IP block
            if line.startswith("SNMP output for"):
                current_ip = line.split()[-1].strip(":")
                snmp_data[current_ip] = {}
                continue

            if ":" in line and current_ip:
                try:

#test multiple

                    prefix_idx, value = line.split(":", 1)
                    prefix = prefix_idx[0].upper()      # S or U
                    idx    = prefix_idx[1:].strip()     # 17
                    val    = value.strip().strip('"')

                    entry = snmp_data[current_ip].setdefault(idx, {})
                    if prefix == "D":
                        entry["descr"] = val
                    elif prefix == "S":
                        entry["admin"] = val
                    elif prefix == "G":
                        entry["speed"] = val
                    elif prefix == "L":
                        entry["link"] = val
                    elif prefix == "M":
                        entry["mtu"] = val
                except ValueError:
                    continue
                    
    return snmp_data



def update_interface_description(device_id, ifindex, description=None, admin=None, link=None, mtu=0, speed=0):
    url = f"{NETBOX_URL}dcim/interfaces/?device_id={device_id}"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to get interfaces for device {device_id}")
        return

    interfaces = resp.json()["results"]
    target_name = f"1/1/{ifindex}"

    for iface in interfaces:
        if iface["name"] == target_name:
            iface_id = iface["id"]
            patch_url = f"{NETBOX_URL}dcim/interfaces/{iface_id}/"

            # Build the payload inside this block
            payload = {}
            if description is not None:
                payload["description"] = description
            if admin is not None:
                payload["enabled"] = admin
            if link is not None:
                payload["mark_connected"] = link
            if mtu is not None:
                payload["mtu"] = mtu
            if speed is not None:
                payload["speed"] = int(speed) * 1000

            # Skip empty payloads
            if not payload:
                print(f"ℹ Nothing to update for {target_name}")
                return

            # -- Dry-run guard -------------------------------------------
            if DRY_RUN:
                print(f"🔎 DRY-RUN  Would PATCH {patch_url}  payload={payload}")
                return
            # ------------------------------------------------------------

            patch_resp = requests.patch(patch_url, headers=headers, json=payload)
            if patch_resp.status_code == 200:
                print(f"✔ Updated {target_name} to: {payload}")
            else:
                print(f"❌ Failed to update {target_name}: {patch_resp.status_code} - {patch_resp.text}")
            break
    else:
        print(f"⚠ Interface {target_name} not found on device {device_id}")

# --- Main logic ---

# Read SNMP results
snmp_map = parse_snmp_output("output.txt")

for ip, iface_data in snmp_map.items():
    print(f"▶ working on {ip}, {len(iface_data)} ports")
    ip_lookup = f"{NETBOX_URL}ipam/ip-addresses/?address={ip}"
    resp = requests.get(ip_lookup, headers=headers)

    if resp.status_code != 200 or not resp.json()["results"]:
        print(f"❌ No match in NetBox for {ip}")
        continue

    ip_data = resp.json()["results"][0]
    device = ip_data.get("assigned_object", {}).get("device")
    if not device:
        print(f"❌ No device linked to IP {ip}")
        continue

    device_id = device["id"]
    device_name = device["name"]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🕒 {timestamp} — {ip} → Device: {device_name}")

    for ifindex, fields in iface_data.items():
        if not ifindex.isdigit() or int(ifindex) > 128:
            continue

        # description (D)
        descr = fields.get("descr")
        if descr:
            print(f"→ D{ifindex}: '{descr}'")

        # admin state (S)
        admin_num = fields.get("admin")
        admin_human = None
        if admin_num:
            admin_human = "true" if admin_num == "1" else \
                          "false" if admin_num == "2" else admin_num
            print(f"→ S{ifindex}: admin={admin_human}")

        # link state (L)
        link_num = fields.get("link")
        link_human = None
        if link_num:
            link_human = "true" if link_num == "1" else \
                         "false" if link_num == "2" else link_num
            print(f"→ L{ifindex}: link={link_human}")

        # MTU (M)
        mtu_val = fields.get("mtu")
        if mtu_val:
            print(f"→ M{ifindex}: '{mtu_val}'")

        # Speed (G)
        speed_val = fields.get("speed")
        if speed_val:
            print(f"→ G{ifindex}: '{speed_val}'")

        update_interface_description(
            device_id,
            ifindex,
            description = fields.get("descr"),
            admin       = admin_human,
            speed       = fields.get("speed"),
            link        = link_human,
            mtu         = fields.get("mtu")
        )

print("---------Python completed.----------")