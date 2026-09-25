#!/usr/bin/env python3
"""Checks for the Debian menu overlay, app catalog, and Debian-specific helpers."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "quickshell/.local/share/omarchy"
OVERLAY = ROOT / "quickshell/.config/omarchy/extensions/omarchy-menu.jsonc"
GENERATOR = ROOT / "tools/generate-debian-menu.py"
CATALOG = RUNTIME / "default/omarchy/debian-apps.conf"


def load_jsonc(path):
    text = "\n".join(line for line in path.read_text().splitlines()
                     if not line.lstrip().startswith("//"))
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", text))


class DebianMenuTests(unittest.TestCase):
    def test_overlay_matches_generator_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "menu.jsonc"
            subprocess.run(["python3", str(GENERATOR), str(output)], check=True,
                           capture_output=True, timeout=30)
            self.assertEqual(output.read_text(), OVERLAY.read_text(),
                             "re-run tools/generate-debian-menu.py")

    def test_overridden_rows_restate_upstream_fields(self):
        # The shell's parser defaults missing fields, so a partial override
        # would erase an action or label.
        default = load_jsonc(RUNTIME / "default/omarchy/omarchy-menu.jsonc")
        overlay = load_jsonc(OVERLAY)
        for item_id, fields in overlay.items():
            if item_id in default:
                for key, value in default[item_id].items():
                    self.assertIn(key, fields, f"{item_id} drops {key}")

    def test_learn_and_arch_only_rows_are_hidden(self):
        overlay = load_jsonc(OVERLAY)
        for item_id in ("learn", "install.aur", "update.channel", "update.config.hyprland",
                        "update.config.shell", "setup.reset"):
            self.assertEqual(overlay[item_id]["when"], "false", item_id)

    def test_system_lock_is_shown(self):
        overlay = load_jsonc(OVERLAY)
        self.assertNotEqual(overlay.get("system.lock", {}).get("when"), "false")

    def test_rows_without_a_working_debian_backend_are_hidden(self):
        overlay = load_jsonc(OVERLAY)
        for item_id in ("trigger.toggle.idle-lock", "setup.config.xcompose",
                        "setup.security.passwordless-sudo"):
            self.assertEqual(overlay[item_id]["when"], "false", item_id)
        self.assertIn("omarchy-cmd-present docker", overlay["setup.security.sudoless-docker"]["when"])

    def test_every_catalog_app_has_install_and_remove_rows(self):
        overlay = load_jsonc(OVERLAY)
        for line in CATALOG.read_text().splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            app_id = line.split("|")[0]
            self.assertIn(f"omarchy-debian-app install {app_id}", overlay[f"install.{app_id}"]["action"])
            self.assertIn(f"omarchy-debian-app remove {app_id}", overlay[f"remove.{app_id}"]["action"])

    def test_overlay_helpers_exist(self):
        text = OVERLAY.read_text()
        for helper in sorted(set(re.findall(r"\b(omarchy-[a-z0-9-]+)", text))):
            self.assertTrue((RUNTIME / "bin" / helper).is_file(), helper)

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_guard_batch_is_valid_bash(self):
        script = """
const fs = require('fs');
const M = require(process.argv[1]);
const d = M.parseMenuJsonc(fs.readFileSync(process.argv[2], 'utf8'));
const u = M.parseMenuJsonc(fs.readFileSync(process.argv[3], 'utf8'));
process.stdout.write(M.guardScript(M.mergeMenuSources(d, u).items));
"""
        guards = subprocess.run(
            ["node", "-e", script, str(RUNTIME / "shell/plugins/menu/MenuModel.js"),
             str(RUNTIME / "default/omarchy/omarchy-menu.jsonc"), str(OVERLAY)],
            check=True, capture_output=True, text=True, timeout=30).stdout
        result = subprocess.run(["bash", "-n"], input=guards, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class DebianHelperTests(unittest.TestCase):
    def test_shell_never_uses_login_shells(self):
        # Debian's /etc/profile resets PATH and drops the private helpers.
        offenders = [str(p.relative_to(RUNTIME)) for p in (RUNTIME / "shell").rglob("*")
                     if p.suffix in (".qml", ".js") and '"-lc"' in p.read_text(errors="ignore")]
        self.assertEqual(offenders, [])
        self.assertNotIn("bash -lc", (RUNTIME / "bin/omarchy-theme-set").read_text())

    def test_ported_helpers_use_lua_hyprctl_forms(self):
        # `hyprctl keyword` and legacy `dispatch exec` are ignored under the
        # Lua config while still exiting 0.
        for name in ("omarchy-restart-shell", "omarchy-system-logout",
                     "omarchy-brightness-display", "omarchy-hyprland-monitor-scaling"):
            text = (RUNTIME / "bin" / name).read_text()
            self.assertNotRegex(text, r"hyprctl keyword monitor|hyprctl dispatch (exec|exit|dpms) ", name)
        self.assertNotIn("hyprctl keyword", (ROOT / "quickshell/.local/bin/quickshell-desktop").read_text())
        self.assertNotIn("hyprctl keyword", (ROOT / "hypr/.config/hypr/screen-rotation.sh").read_text())

    def test_catalog_lookup(self):
        env = dict(os.environ, OMARCHY_PATH=str(RUNTIME), PATH=f"{RUNTIME / 'bin'}:{os.environ['PATH']}")
        listing = subprocess.run(["bash", str(RUNTIME / "bin/omarchy-debian-app"), "list"],
                                 env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(listing.returncode, 0, listing.stderr)
        self.assertIn("browser.zen", listing.stdout)
        missing = subprocess.run(["bash", str(RUNTIME / "bin/omarchy-debian-app"), "present", "no.such.app"],
                                 env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(missing.returncode, 1)

    def test_router_usage_counts_sessions_without_a_key(self):
        with tempfile.TemporaryDirectory() as home:
            sessions = Path(home) / ".pi/agent/sessions/x"
            sessions.mkdir(parents=True)
            lines = [
                {"type": "message", "message": {"role": "user", "timestamp": 1789307011770}},
                {"type": "message", "message": {"role": "assistant", "provider": "openrouter", "model": "m",
                                                "timestamp": 1789307012000,
                                                "usage": {"input": 10, "output": 5, "cacheRead": 0, "cacheWrite": 0}}},
            ]
            (sessions / "s.jsonl").write_text("\n".join(json.dumps(l) for l in lines) + "\n")
            env = {k: v for k, v in os.environ.items() if k not in ("OPENROUTER_API_KEY", "XDG_DATA_HOME")}
            env["HOME"] = home
            result = subprocess.run(["python3", str(RUNTIME / "bin/omarchy-debian-router-usage"), "openrouter"],
                                    env=env, capture_output=True, text=True, timeout=30)
            record = json.loads(result.stdout)
            self.assertEqual(record["name"], "OpenRouter")
            self.assertEqual(record["totalPrompts"], 1)
            self.assertEqual(record["modelUsage"]["m"]["inputTokens"], 10)
            self.assertIn("OPENROUTER_API_KEY", record["authHelpText"])

    def test_uwsm_shim_runs_the_command(self):
        result = subprocess.run(["bash", str(RUNTIME / "bin/uwsm-app"), "--", "printf", "ok"],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.stdout, "ok")

    def test_terminal_wrapper_answers_print_id(self):
        with tempfile.TemporaryDirectory() as home:
            env = dict(os.environ, HOME=home, XDG_CONFIG_HOME=f"{home}/.config")
            result = subprocess.run(["bash", str(RUNTIME / "bin/xdg-terminal-exec"), "--print-id"],
                                    env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.stdout.strip(), "kitty.desktop")

    def fake_bin(self, tmp, scripts):
        bin_dir = Path(tmp) / "fake-bin"
        bin_dir.mkdir()
        for name, body in scripts.items():
            path = bin_dir / name
            path.write_text("#!/bin/bash\n" + body + "\n")
            path.chmod(0o755)
        return bin_dir

    def test_launcher_uninstall_resolves_the_debian_package(self):
        self.assertNotIn("pacman", (RUNTIME / "bin/omarchy-remove-launcher-entry").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            apps = Path(tmp) / "share/applications"
            apps.mkdir(parents=True)
            (apps / "foo.desktop").write_text("[Desktop Entry]\nName=Foo\nExec=foo %U\n")
            bin_dir = self.fake_bin(tmp, {
                "dpkg-query": 'echo "foo-pkg:amd64, other: $2"',
                "omarchy-launch-floating-terminal-with-presentation": 'printf "%s\\n" "$*"',
            })
            env = dict(os.environ, XDG_DATA_HOME=f"{tmp}/user", XDG_DATA_DIRS=f"{tmp}/share",
                       PATH=f"{bin_dir}:{RUNTIME / 'bin'}:{os.environ['PATH']}")
            result = subprocess.run(["bash", str(RUNTIME / "bin/omarchy-remove-launcher-entry"), "foo", "Foo"],
                                    env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("sudo apt remove foo-pkg", result.stdout)

    def test_share_opens_the_localsend_gui(self):
        self.assertNotIn("localsend --headless", (RUNTIME / "bin/omarchy-menu-share").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = self.fake_bin(tmp, {"systemd-run": 'printf "%s\\n" "$*"', "localsend_app": ""})
            env = dict(os.environ, PATH=f"{bin_dir}:{RUNTIME / 'bin'}:{os.environ['PATH']}")
            result = subprocess.run(["bash", str(RUNTIME / "bin/omarchy-menu-share"), "file", "/tmp/a b.txt"],
                                    env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "--user --quiet --collect localsend_app /tmp/a b.txt")

    def test_screenrecording_creates_a_missing_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            # No recording is active, so --stop-recording exits right after the
            # directory check without touching wf-recorder.
            bin_dir = self.fake_bin(tmp, {"pgrep": "exit 1", "omarchy-notification-send": ""})
            target = Path(tmp) / "Videos"
            env = dict(os.environ, HOME=tmp, OMARCHY_SCREENRECORD_DIR=str(target),
                       PATH=f"{bin_dir}:{RUNTIME / 'bin'}:{os.environ['PATH']}")
            subprocess.run(["bash", str(RUNTIME / "bin/omarchy-capture-screenrecording"), "--stop-recording"],
                           env=env, capture_output=True, text=True, timeout=10)
            self.assertTrue(target.is_dir())

    def test_debian_session_fixes(self):
        self.assertIn("/usr/sbin", (ROOT / "quickshell/.local/bin/quickshell-desktop").read_text())
        app_library = (RUNTIME / "shell/services/AppLibrary.qml").read_text()
        self.assertIn("runInTerminal", app_library)
        self.assertIn("xdg-terminal-exec", app_library)
        self.assertIn("initramfs-tools", (RUNTIME / "bin/omarchy-hibernation-available").read_text())
        self.assertNotIn("pacman", (RUNTIME / "bin/omarchy-version-pkgs").read_text())

    def test_fastfetch_config_has_no_arch_helpers(self):
        config = ROOT / "fastfetch/etc/fastfetch/config.jsonc"
        text = config.read_text()
        json.loads(text)
        self.assertIn("~/.config/omarchy/branding/about.txt", text)
        self.assertTrue((ROOT / "quickshell/.config/omarchy/branding/about.txt").is_file())
        for arch_only in ("omarchy-version)", "omarchy-version-branch", "omarchy-version-channel", "echo -e"):
            self.assertNotIn(arch_only, text)

    def test_arch_package_names_are_translated(self):
        result = subprocess.run(["bash", str(RUNTIME / "bin/omarchy-pkg-debian-name"), "openssh", "pam-u2f", "curl"],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.stdout.split(), ["openssh-server", "libpam-u2f", "curl"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
