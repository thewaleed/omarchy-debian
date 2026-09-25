#!/usr/bin/env python3
"""Generate the Debian overlay for the Omarchy menu.

Reads Omarchy's shipped menu and the Debian app catalog, then writes
quickshell/.config/omarchy/extensions/omarchy-menu.jsonc, which the shell
merges over the defaults. Re-run after editing the catalog or the rules below:

    python3 ~/dotfils/tools/generate-debian-menu.py
"""

import json
import re
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "quickshell/.local/share/omarchy"
DEFAULT_MENU = RUNTIME / "default/omarchy/omarchy-menu.jsonc"
CATALOG = RUNTIME / "default/omarchy/debian-apps.conf"
OUTPUT = ROOT / "quickshell/.config/omarchy/extensions/omarchy-menu.jsonc"

PRESENT = "omarchy-launch-floating-terminal-with-presentation"

# Rows that have no Debian equivalent, would damage this setup, or depend on
# checkpoints that are not finished yet. Hiding a submenu's every row hides it.
HIDDEN = {
    "learn": "removed at the user's request",
    "trigger.hardware.hybrid-gpu": "Arch supergfxctl integration",
    "trigger.toggle.crash-capture": "crash watcher service is not installed",
    "trigger.capture.screenrecord.webcam": "webcam overlay not ported to wf-recorder",
    "trigger.toggle.idle-lock": "no-op while the lock plugin is disabled (lock/idle checkpoint)",
    "setup.config.xcompose": "fcitx5 is not installed, so there is nothing to restart",
    "setup.security.passwordless-sudo": "sudo is already passwordless via /etc/sudoers.d/99-thewaleed",
    "style.unlock": "Plymouth is not used on this system",
    "setup.direct-boot": "Arch Limine/UKI boot setup",
    "setup.reset": "Arch factory reset",
    "setup.security.fingerprint": "no fingerprint reader",
    "setup.default.browser.brave-origin": "no Debian source",
    "setup.default.terminal.ghostty": "no Debian source",
    "setup.default.editor.cursor": "no Debian source",
    "setup.default.editor.helix": "no Debian source",
    "update.channel": "Omarchy release channels are Arch-only",
    "update.config.hyprland": "would overwrite the Stow-managed ~/.config/hypr",
    "update.config.shell": "would reset shell.json and re-enable lock/idle",
    "update.config.plymouth": "Plymouth is not used on this system",
    "install.aur": "Arch User Repository",
    "install.windows": "Arch Windows VM helper",
    "install.preinstalls": "Arch preinstall bundle",
    "remove.windows": "Arch Windows VM helper",
    "remove.preinstalls": "Arch preinstall bundle",
}

# Upstream Install/Remove rows kept as they are (they work on Debian).
KEEP = {
    "install.package", "install.style", "install.style.theme",
    "install.style.background", "install.style.font", "install.webapp",
    "install.tui", "install.gaming.geforce-now", "install.gaming.xbox-cloud",
    "install.gaming.retro-launcher", "install.development.docker-dbs",
    "remove.package", "remove.theme", "remove.webapp", "remove.tui",
    "remove.security", "remove.security.fido2", "remove.security.sshd",
    "remove.security.sudoless-docker", "remove.security.fingerprint",
    "remove.gaming.geforce-now", "remove.gaming.xbox-cloud",
}

# Overrides applied after the catalog wiring.
OVERRIDES = {
    "update.omarchy": {
        "icon": "\uf306", "iconFont": "", "label": "System",
        "description": "APT full-upgrade and Flatpak update",
        "action": "omarchy-debian-update",
    },
    "update.password.drive": {"when": "lsblk -rno TYPE | grep -qx crypt"},
    "trigger.share.receive": {"action": "localsend_app", "when": "omarchy-cmd-present localsend_app"},
    "trigger.capture.screenrecord.stop": {"when": "pgrep -f '^wf-recorder'"},
    "install.development.docker-dbs": {"when": "omarchy-cmd-present docker"},
    "install.gaming.retro-launcher": {"when": "omarchy-cmd-present retroarch"},
    "remove.security.sshd": {"when": "systemctl is-enabled --quiet ssh"},
    "setup.security.sudoless-docker": {"when": "omarchy-cmd-present docker && omarchy-sudo-docker --configured"},
    "install.flatpak": {
        "icon": "\U000f03d7", "label": "Flatpak",
        "action": "xdg-terminal-exec --app-id=org.omarchy.terminal omarchy-flatpak-install",
    },
    "remove.flatpak": {
        "icon": "\U000f03d7", "label": "Flatpak",
        "action": "xdg-terminal-exec --app-id=org.omarchy.terminal omarchy-flatpak-remove",
    },
}

# Nerd Font rows: dim them once the family is installed.
FONT_FAMILY = re.compile(r"omarchy-install-font\s+(?:'[^']*'|\S+)\s+\S+\s+'?([^']+?)'?$")

# Icons and parent labels for catalog rows that upstream does not have.
NEW_ICONS = {
    "browser.chromium": "\uf268", "editor.neovim": "\uf36f", "development.docker": "\uf308",
    "editor.antigravity": "\U000f0b3f", "editor.mousepad": "\uf15c",
    "files.nautilus": "\uf07b", "files.thunar": "\uf07b",
    "ai.claude-code": "\U000f06c4", "ai.opencode": "\uf120", "ai.hermes-agent": "\U000f06a9", "ai.herdr": "\uf489",
}
# Submenus neither side of upstream has.
EXTRA_PARENTS = {
    "install.files": {"icon": "\uf07c", "label": "File Manager"},
    "remove.files": {"icon": "\uf07c", "label": "File Manager"},
}
# Remove submenus that upstream lacks reuse the matching Install row's icon.
NEW_PARENTS = ("remove.editor", "remove.terminal")


def load_jsonc(path):
    text = "\n".join(line for line in path.read_text().splitlines()
                     if not line.lstrip().startswith("//"))
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", text))


def load_catalog():
    entries = {}
    for line in CATALOG.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        app_id, label, method, packages, source = line.split("|")
        entries[app_id] = {"label": label, "method": method,
                           "packages": packages.split(), "source": source}
    return entries


def presence(app_id, entry):
    """Fast menu guard: the shell answers omarchy-pkg-present in-process."""
    custom = {
        "development.php.laravel": "[[ -x $HOME/.config/composer/vendor/bin/laravel ]]",
        "development.elixir.phoenix": 'compgen -G "$HOME/.mix/archives/phx_new*"',
        "ai.claude-code": "omarchy-cmd-present claude",
        "ai.opencode": "omarchy-cmd-present opencode",
        "ai.hermes-agent": "omarchy-cmd-present hermes",
        "ai.herdr": "omarchy-cmd-present herdr",
    }
    if app_id in custom:
        return custom[app_id]
    return f"omarchy-pkg-present {entry['packages'][0]}"


def main():
    menu = load_jsonc(DEFAULT_MENU)
    catalog = load_catalog()
    out = {}
    notes = {}

    def put(item_id, fields, note=None):
        out.setdefault(item_id, {}).update(fields)
        if note:
            notes[item_id] = note

    for item_id, reason in HIDDEN.items():
        put(item_id, {"when": "false"}, reason)

    # Install/Remove: wire catalog apps, hide everything else without a source.
    for item_id, item in menu.items():
        section, _, rest = item_id.partition(".")
        if section not in ("install", "remove") or not rest:
            continue
        if item_id in KEEP or item_id in HIDDEN or item_id.startswith("install.style.font."):
            continue
        if "action" not in item and "provider" not in item:
            continue  # submenu: disappears when all of its rows are hidden
        if rest not in catalog:
            put(item_id, {"when": "false"}, "no Debian source")

    for app_id, entry in catalog.items():
        guard = presence(app_id, entry)
        install = {
            "label": entry["label"],
            "action": f"{PRESENT} {shlex.quote('omarchy-debian-app install ' + app_id)}",
            "disabled": guard,
        }
        remove = {
            "label": entry["label"],
            "action": f"{PRESENT} {shlex.quote('omarchy-debian-app remove ' + app_id)}",
            "when": guard,
        }
        # Install rows dim once installed; Remove rows hide until installed.
        for side, fields in (("install", install), ("remove", remove)):
            item_id = f"{side}.{app_id}"
            if item_id not in menu:
                twin = menu.get(f"install.{app_id}", {})
                fields["icon"] = twin.get("icon", NEW_ICONS.get(app_id, ""))
                if "iconFont" in twin:
                    fields["iconFont"] = twin["iconFont"]
            put(item_id, fields)

    for item_id, fields in EXTRA_PARENTS.items():
        put(item_id, fields)

    for item_id in NEW_PARENTS:
        source = menu["install." + item_id.split(".", 1)[1]]
        put(item_id, {k: source[k] for k in ("icon", "iconFont", "label") if k in source})

    # Default agents: only offer agents that are already installed (upstream
    # installs them with mise, which Debian does not ship).
    for item_id, item in menu.items():
        if item_id.startswith("setup.default.agent.") and "action" in item:
            agent = item["action"].split()[-1]
            put(item_id, {"when": f"omarchy-cmd-present {agent}"})

    for item_id, item in menu.items():
        if item_id.startswith("install.style.font.") and "action" in item:
            match = FONT_FAMILY.search(item["action"])
            if match:
                put(item_id, {"disabled": f"fc-list : family | grep -qF {shlex.quote(match.group(1))}"})

    for item_id, fields in OVERRIDES.items():
        put(item_id, fields)

    # The shell's overlay parser fills every field an entry leaves out with a
    # default (empty action, label = id), so an override must restate the
    # whole upstream row, not just the fields it changes.
    for item_id in out:
        if item_id in menu:
            out[item_id] = {**menu[item_id], **out[item_id]}

    lines = [
        "{",
        "  // GENERATED by ~/dotfils/tools/generate-debian-menu.py; edit that script",
        "  // or default/omarchy/debian-apps.conf, then re-run it.",
        "  //",
        "  // Debian overlay for the Omarchy menu: hides Arch-only rows, routes",
        "  // Install/Remove through omarchy-debian-app, and adds Debian entries.",
    ]
    for item_id in sorted(out, key=lambda k: (k.split(".")[0], k)):
        if item_id in notes:
            lines.append(f"  // {notes[item_id]}")
        lines.append(f"  {json.dumps(item_id)}: {json.dumps(out[item_id], ensure_ascii=False)},")
    lines.append("}")
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")
    print(f"wrote {len(out)} entries to {output}")


if __name__ == "__main__":
    main()
