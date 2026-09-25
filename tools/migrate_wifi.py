#!/usr/bin/python3
"""One-machine, reversible ifupdown -> NetworkManager WPA-PSK migration.

Credentials are read in memory and stored only in root-private backup/keyfiles.
They are never passed as process arguments or printed.
"""

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import subprocess
import tempfile
import time
import uuid


BACKUP = Path("/var/backups/quickshell-wifi")
INTERFACES = Path("/etc/network/interfaces")
CONNECTIONS = Path("/etc/NetworkManager/system-connections")
RECOVERY_CONF = Path("/etc/NetworkManager/conf.d/91-quickshell-ifupdown-recovery.conf")
RECOVERY_MARKER = "# Managed by the Quickshell Wi-Fi migration rollback.\n"


def parse_interfaces(text, iface):
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines)
              if line.split()[:4] == ["iface", iface, "inet", "dhcp"]]
    if len(starts) != 1:
        raise ValueError("Expected exactly one DHCP stanza for the Wi-Fi interface")
    start = starts[0]
    end = start + 1
    fields = {}
    declarations = {"iface", "auto", "allow-hotplug", "mapping", "source", "source-directory"}
    while end < len(lines):
        parts = lines[end].strip().split(None, 1)
        if parts and parts[0] in declarations:
            break
        if parts and not parts[0].startswith("#"):
            if len(parts) != 2 or parts[0] not in {"wpa-ssid", "wpa-psk"}:
                raise ValueError("Additional interface options require manual review")
            value = parts[1]
            if value.startswith(('"', "'")):
                tokens = shlex.split(value)
                if len(tokens) != 1:
                    raise ValueError("Unsupported quoted Wi-Fi value")
                value = tokens[0]
            fields[parts[0]] = value
        end += 1
    ssid, psk = fields.get("wpa-ssid", ""), fields.get("wpa-psk", "")
    if not 1 <= len(ssid.encode()) <= 32:
        raise ValueError("Invalid or missing SSID")
    if not (8 <= len(psk) <= 63 or re.fullmatch(r"[0-9a-fA-F]{64}", psk)):
        raise ValueError("Invalid or missing WPA-PSK")
    kept = []
    for index, line in enumerate(lines):
        if start <= index < end:
            continue
        parts = line.split()
        if parts and parts[0] in {"auto", "allow-hotplug"} and iface in parts[1:]:
            parts = [part for part in parts if part != iface]
            if len(parts) > 1:
                kept.append(" ".join(parts) + "\n")
        else:
            kept.append(line)
    return ssid, psk, "".join(kept)


def run(*args, check=True, timeout=30):
    result = subprocess.run(args, text=True, capture_output=True, timeout=timeout,
                            env={**os.environ, "PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C"})
    if check and result.returncode:
        raise RuntimeError(f"{Path(args[0]).name} failed with exit {result.returncode}")
    return result


def write_private(path, data):
    descriptor, filename = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    temp = Path(filename)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data if isinstance(data, bytes) else data.encode())
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def save_state(state):
    write_private(BACKUP / "state.json", json.dumps(state, indent=2) + "\n")


def prepare(iface):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", iface):
        raise ValueError("Invalid interface name")
    if BACKUP.exists():
        raise RuntimeError("A migration backup already exists; inspect it before repeating")
    if INTERFACES.is_symlink():
        raise RuntimeError("Symlinked interfaces file requires manual review")
    original = INTERFACES.read_bytes()
    ssid, psk, remaining = parse_interfaces(original.decode(), iface)
    from gi.repository import GLib
    identifier = str(uuid.uuid4())
    keyfile = GLib.KeyFile()
    values = {
        "connection": {"id": "Primary Wi-Fi", "uuid": identifier, "type": "wifi",
                       "interface-name": iface, "autoconnect": "true", "autoconnect-priority": "10"},
        "wifi": {"mode": "infrastructure", "ssid": ssid},
        "wifi-security": {"key-mgmt": "wpa-psk", "psk": psk, "psk-flags": "0"},
        "ipv4": {"method": "auto"}, "ipv6": {"method": "auto"},
    }
    for group, properties in values.items():
        for key, value in properties.items():
            keyfile.set_string(group, key, value)
    BACKUP.mkdir(mode=0o700)
    write_private(BACKUP / "interfaces.original", original)
    write_private(BACKUP / "interfaces.networkmanager", remaining)
    write_private(BACKUP / "wifi.nmconnection", keyfile.to_data()[0])
    shutil.copyfile(__file__, BACKUP / "migrate_wifi.py")
    os.chmod(BACKUP / "migrate_wifi.py", 0o700)
    save_state({"status": "prepared", "interface": iface, "uuid": identifier,
                "keyfile": f"quickshell-{identifier}.nmconnection"})
    print(f"Prepared migration for {iface}. Private backup: {BACKUP}")


def rollback(state):
    iface = state["interface"]
    original = (BACKUP / "interfaces.original").read_bytes()
    migrated = (BACKUP / "interfaces.networkmanager").read_bytes()
    if INTERFACES.read_bytes() not in {original, migrated}:
        raise RuntimeError("Interfaces changed since migration; review before rollback")
    if RECOVERY_CONF.exists() and not RECOVERY_CONF.read_text().startswith(RECOVERY_MARKER):
        raise RuntimeError("An unrelated recovery configuration already exists")
    # Keep the legacy interface out of NetworkManager after a reboot too,
    # even if the main ifupdown plugin setting has been changed to managed=true.
    write_private(RECOVERY_CONF, RECOVERY_MARKER +
                  f"[device-quickshell-ifupdown-recovery]\nmatch-device=interface-name:{iface}\nmanaged=0\n")
    run("nmcli", "--wait", "10", "connection", "down", "uuid", state["uuid"], check=False)
    run("nmcli", "device", "set", iface, "managed", "no", check=False)
    write_private(INTERFACES, original)
    run("nmcli", "connection", "delete", "uuid", state["uuid"], check=False)
    (CONNECTIONS / state["keyfile"]).unlink(missing_ok=True)
    run("nmcli", "general", "reload", "conf", check=False)
    # Keep restored supplicant/DHCP processes in networking.service, not in
    # this transient migration unit (which kills its children when it exits).
    run("systemctl", "restart", "networking.service", timeout=75)
    state["status"] = "rolled-back"
    save_state(state)
    print("Restored the original ifupdown configuration.")


def apply(state):
    if state["status"] not in {"prepared", "rolled-back"}:
        raise RuntimeError("Migration is not in the prepared state")
    if INTERFACES.read_bytes() != (BACKUP / "interfaces.original").read_bytes():
        raise RuntimeError("Network configuration changed after preparation")
    if RECOVERY_CONF.exists():
        if not RECOVERY_CONF.read_text().startswith(RECOVERY_MARKER):
            raise RuntimeError("An unrelated recovery configuration already exists")
        RECOVERY_CONF.unlink()
    iface = state["interface"]
    target = CONNECTIONS / state["keyfile"]
    if target.exists():
        raise RuntimeError("Destination connection already exists")
    write_private(target, (BACKUP / "wifi.nmconnection").read_bytes())
    run("nmcli", "connection", "load", str(target))
    run("systemd-run", "--collect", "--unit=quickshell-wifi-rollback", "--on-active=300s",
        "/usr/bin/python3", "-I", str(BACKUP / "migrate_wifi.py"), "rollback-if-pending")
    state["status"] = "switching"
    save_state(state)
    try:
        run("ifdown", iface, timeout=45)
        write_private(INTERFACES, (BACKUP / "interfaces.networkmanager").read_bytes())
        # A conf/connections reload alone can retain ifupdown's strict
        # unmanaged decision. Restart after removing the legacy stanza.
        run("systemctl", "restart", "NetworkManager.service", timeout=45)
        run("nmcli", "device", "set", iface, "managed", "yes")
        for _ in range(30):
            device_state = run("nmcli", "-g", "GENERAL.STATE", "device", "show", iface).stdout
            if device_state.split() and int(device_state.split()[0]) >= 30:
                break
            time.sleep(1)
        else:
            raise RuntimeError("Wi-Fi did not become available to NetworkManager")
        run("nmcli", "--wait", "60", "connection", "up", "uuid", state["uuid"], "ifname", iface, timeout=70)
        status = run("nmcli", "-g", "GENERAL.STATE", "device", "show", iface).stdout
        if not status.startswith("100"):
            raise RuntimeError("NetworkManager did not establish the Wi-Fi connection")
        connected = False
        for _ in range(6):
            try:
                with socket.create_connection(("deb.debian.org", 443), timeout=8):
                    connected = True
                    break
            except OSError:
                time.sleep(3)
        if not connected:
            raise RuntimeError("Connectivity check failed after the handover")
        state["status"] = "complete"
        save_state(state)
        run("systemctl", "stop", "quickshell-wifi-rollback.timer", check=False)
        print("NetworkManager Wi-Fi handover completed; DNS and outbound connectivity verified.")
    except Exception:
        print("Handover failed; restoring the original connection.", flush=True)
        rollback(state)
        run("systemctl", "stop", "quickshell-wifi-rollback.timer", check=False)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "apply", "rollback", "rollback-if-pending", "status"])
    parser.add_argument("--interface", default="wlp3s0")
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error("Run through sudo; credentials and backups must remain root-private")
    os.umask(0o077)
    if args.action == "prepare":
        prepare(args.interface)
        return
    state = json.loads((BACKUP / "state.json").read_text())
    if args.action == "apply":
        apply(state)
    elif args.action == "rollback":
        rollback(state)
    elif args.action == "rollback-if-pending":
        if state["status"] == "switching":
            rollback(state)
    else:
        print(json.dumps(state, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Avoid tracebacks containing credential-bearing input or file content.
        print(f"Migration stopped: {type(error).__name__}: {error}", flush=True)
        raise SystemExit(1)
