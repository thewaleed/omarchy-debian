"""Non-destructive checks for the Stow-managed Debian integration."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "quickshell/.local/share/omarchy"
ENTRY = ROOT / "quickshell/.local/bin/quickshell-desktop"


class PortTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="quickshell-port-")
        self.addCleanup(self.scratch.cleanup)
        self.base = Path(self.scratch.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), PATH=f"{self.bin}:/usr/bin:/bin")

    def stub(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/bash\n" + body + "\n")
        path.chmod(0o700)
        return path

    def run_script(self, path, *args):
        return subprocess.run(["/bin/bash", str(path), *args], env=self.env,
                              capture_output=True, text=True, timeout=25)

    def test_stow_config_is_resolved_before_launch(self):
        runtime = self.home / ".local/share/omarchy/bin"
        runtime.mkdir(parents=True)
        config = self.home / ".config/omarchy"
        config.mkdir(parents=True)
        source = self.base / "source-shell.json"
        source.write_text('{"version": 1}\n')
        destination = config / "shell.json"
        destination.symlink_to(source)
        launcher = runtime / "omarchy-launch-shell"
        launcher.write_text('#!/bin/bash\nprintf "%s\\n" "$OMARCHY_SHELL_CONFIG"\n')
        launcher.chmod(0o700)
        result = self.run_script(ENTRY, "start")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(source))
        self.assertTrue(destination.is_symlink())

    def test_update_status_and_errors_are_distinct(self):
        for output, exit_code, expected in [
            ("Inst example [1.0] (2.0 Debian)\n", 0, 0),
            ("0 upgraded, 0 newly installed, 0 to remove.\n", 0, 1),
            ("", 100, 2),
        ]:
            with self.subTest(expected=expected):
                self.env.update(FAKE_OUTPUT=output, FAKE_STATUS=str(exit_code),
                                ARG_LOG=str(self.base / "apt-args"))
                self.stub("apt-get", 'printf "%s\\n" "$@" > "$ARG_LOG"\n'
                          'printf "%s" "$FAKE_OUTPUT"\nexit "$FAKE_STATUS"')
                result = self.run_script(RUNTIME / "bin/omarchy-update-available")
                self.assertEqual(result.returncode, expected, result.stderr)
                args = (self.base / "apt-args").read_text().splitlines()
                self.assertIn("--simulate", args)
                self.assertNotIn("update", args)

    def test_file_picker_skips_missing_search_paths(self):
        # Trigger > Transcode searches ~/Pictures:~/Videos; this home has no ~/Videos.
        pictures = self.home / "Pictures"
        pictures.mkdir()
        (pictures / "shot.png").write_bytes(b"")
        self.stub("omarchy-menu-select", "cat")
        picker = RUNTIME / "bin/omarchy-menu-file"

        result = self.run_script(picker, "Pick", f"{pictures}:{self.home / 'Videos'}", "png mp4")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [str(pictures / "shot.png")])

        result = self.run_script(picker, "Pick", str(self.home / "Videos"), "mp4")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Path not found", result.stderr)

    def test_debian_package_guards_include_provides_but_not_removed_packages(self):
        self.env["PATH"] = f"{RUNTIME / 'bin'}:{self.bin}:/usr/bin:/bin"
        self.stub("dpkg-query", '''printf '%s\\n' \
'google-chrome-stable\tinstalled\twww-browser' \
'libexample:amd64\tinstalled\tvirtual-example (= 2), another-provider' \
'removed-example\tconfig-files\t' ''')
        for name in ("google-chrome", "www-browser", "libexample", "virtual-example"):
            with self.subTest(package=name):
                result = self.run_script(RUNTIME / "bin/omarchy-pkg-present", name)
                self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_script(RUNTIME / "bin/omarchy-pkg-present", "removed-example")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.run_script(RUNTIME / "bin/omarchy-pkg-present").returncode, 0)
        self.assertEqual(self.run_script(RUNTIME / "bin/omarchy-pkg-missing").returncode, 1)

    def test_scaling_applies_with_lua_and_persists_in_monitors_lua(self):
        self.env["COMMAND_LOG"] = str(self.base / "hyprctl-args")
        self.stub("hyprctl", '''
if [[ $1 == monitors ]]; then
  printf '%s\\n' '[{"name":"eDP-1","focused":true,"scale":1.5,"width":1920,"height":1080,"refreshRate":60,"x":0,"y":0,"transform":0,"mirrorOf":"none"}]'
else
  printf '%s\\n' "$@" > "$COMMAND_LOG"
fi
''')
        self.stub("omarchy-notification-send", "exit 0")
        self.stub("omarchy-shell", "exit 0")
        monitors = self.home / ".config/hypr/monitors.lua"
        monitors.parent.mkdir(parents=True)
        monitors.write_text((ROOT / "hypr/.config/hypr/monitors.lua").read_text())
        result = self.run_script(RUNTIME / "bin/omarchy-hyprland-monitor-scaling", "2")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = (self.base / "hyprctl-args").read_text().splitlines()
        self.assertEqual(args[0], "eval")
        self.assertIn('hl.monitor({ output = "eDP-1"', args[1])
        self.assertIn("scale = 2 })", args[1])
        text = monitors.read_text()
        self.assertIn('position = "auto", scale = 2 })', text)
        self.assertIn('hl.env("GDK_SCALE", "2")', text)

    def prepare_dns(self):
        self.env["DNS_LOG"] = str(self.base / "dns-commands")
        self.stub("ip", '''printf '%s\\n' '[{"dev":"CloudflareWARP","metric":0},{"dev":"wlp3s0","metric":600}]' ''')
        self.stub("nmcli", '''
if [[ $1 == -g && $2 == GENERAL.CON-UUID ]]; then
  printf 'physical-profile-uuid\\n'
else
  printf '%s\\n' "$*" >> "$DNS_LOG"
fi
''')

    def test_dns_changes_only_the_physical_profile_without_restarting_warp(self):
        self.prepare_dns()
        result = self.run_script(RUNTIME / "bin/omarchy-dns", "Google")
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = (self.base / "dns-commands").read_text()
        self.assertIn("connection modify physical-profile-uuid", commands)
        self.assertIn("ipv4.dns 8.8.8.8,8.8.4.4", commands)
        self.assertIn("device reapply wlp3s0", commands)
        self.assertNotIn("CloudflareWARP", commands)

    def test_invalid_custom_dns_does_not_modify_connection(self):
        self.prepare_dns()
        result = self.run_script(RUNTIME / "bin/omarchy-dns", "Custom", "not-an-address")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.base / "dns-commands").exists())

    def prepare_restart(self, locked=False):
        self.env.update(OMARCHY_PATH=str(RUNTIME), HYPRLAND_INSTANCE_SIGNATURE="test-only",
                        EVENT_LOG=str(self.base / "events"), STATE_FILE=str(self.base / "state"))
        self.stub("systemctl", "exit 0")
        self.stub("omarchy-hyprland-session-locked", f"exit {0 if locked else 1}")
        self.stub("omarchy-shell", 'printf \'{"secure":true,"requested":true}\\n\'')
        self.stub("hyprctl", 'printf "launch:%s\\n" "$*" >> "$EVENT_LOG"; echo ok')

    def test_restart_waits_for_asynchronous_exit(self):
        self.prepare_restart()
        self.stub("quickshell", '''
if [[ $1 == "list" ]]; then
  n=0
  [[ ! -f $STATE_FILE ]] || read -r n < "$STATE_FILE"
  n=$((n + 1))
  printf '%s\\n' "$n" > "$STATE_FILE"
  printf 'list:%s\\n' "$n" >> "$EVENT_LOG"
  if (( n < 3 )); then printf '[{"pid":123}]\\n'; else printf '[]\\n'; fi
else
  printf 'kill\\n' >> "$EVENT_LOG"
fi
''')
        result = self.run_script(RUNTIME / "bin/omarchy-restart-shell")
        self.assertEqual(result.returncode, 0, result.stderr)
        events = (self.base / "events").read_text().splitlines()
        self.assertLess(events.index("list:3"), next(i for i, v in enumerate(events) if v.startswith("launch:")))
        self.assertEqual(sum(v.startswith("launch:") for v in events), 1)
        self.assertIn("dispatch hl.dsp.exec_cmd(", events[-1])

    def test_restart_handles_quickshell_030_empty_list_message(self):
        self.prepare_restart()
        self.stub("quickshell", 'printf \'No running instances for "test/shell.qml"\\nUse --all to list all instances.\\n\'')
        result = self.run_script(RUNTIME / "bin/omarchy-restart-shell")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("dispatch hl.dsp.exec_cmd(", (self.base / "events").read_text())

    def test_restart_refuses_to_replace_a_secure_locker(self):
        self.prepare_restart(locked=True)
        self.stub("quickshell", 'printf "unexpected\\n" >> "$EVENT_LOG"\nexit 1')
        result = self.run_script(RUNTIME / "bin/omarchy-restart-shell")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing to restart", result.stderr)
        self.assertFalse((self.base / "events").exists())

    def test_core_and_plugin_components_compile_without_instantiation(self):
        display = os.environ.get("WAYLAND_DISPLAY")
        session_runtime = os.environ.get("XDG_RUNTIME_DIR")
        if not display or not session_runtime:
            self.skipTest("PanelWindow type compilation requires a Wayland backend")
        display_socket = Path(session_runtime) / display
        if not display_socket.is_socket():
            self.skipTest("Wayland display socket is unavailable")
        components = {"shell.qml", "plugins/bar/Bar.qml", "services/AppLibrary.qml"}
        shell = RUNTIME / "shell"
        for manifest in (shell / "plugins").rglob("*manifest.json"):
            data = json.loads(manifest.read_text())
            for entry in data.get("entryPoints", {}).values():
                path = manifest.parent / entry
                if path.suffix == ".qml":
                    components.add(str(path.relative_to(shell)))
        runtime = self.base / "runtime"
        runtime.mkdir(mode=0o700)
        self.env.update(
            OMARCHY_PATH=str(RUNTIME), OMARCHY_CHECK_COMPONENTS=json.dumps(sorted(components)),
            QT_QPA_PLATFORM="wayland", QT_QUICK_BACKEND="software", QML_DISABLE_DISK_CACHE="1",
            WAYLAND_DISPLAY=str(display_socket),
            XDG_RUNTIME_DIR=str(runtime), XDG_CONFIG_HOME=str(self.home / ".config"),
            XDG_CACHE_HOME=str(self.home / ".cache"), XDG_STATE_HOME=str(self.home / ".local/state"),
            XDG_DATA_HOME=str(self.home / ".local/share"),
            DBUS_SESSION_BUS_ADDRESS=f"unix:path={self.base}/no-session-bus",
            DBUS_SYSTEM_BUS_ADDRESS=f"unix:path={self.base}/no-system-bus",
        )
        for variable in ("DISPLAY", "HYPRLAND_INSTANCE_SIGNATURE"):
            self.env.pop(variable, None)
        result = subprocess.run(
            ["/usr/bin/quickshell", "--no-color", "--path", str(shell / "debian-compatibility-check.qml")],
            env=self.env, capture_output=True, text=True, timeout=45,
        )
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("DEBIAN_COMPONENT_CHECK_OK", output)
        self.assertNotIn("COMPONENT_FAILED", output)
        print(f"Compiled {len(components)} shell/plugin entry points without instantiating them.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
