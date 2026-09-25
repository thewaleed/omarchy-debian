#!/usr/bin/env python3
"""Checks for the Stow-managed Hyprland Lua configuration."""

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HYPR = ROOT / "hypr/.config/hypr"
RUNTIME = ROOT / "quickshell/.local/share/omarchy"


class HyprConfigTests(unittest.TestCase):
    def test_owned_modules_do_not_use_uwsm(self):
        for path in HYPR.glob("*.lua"):
            code = "\n".join(line for line in path.read_text().splitlines()
                             if not line.lstrip().startswith("--"))
            self.assertNotIn("uwsm", code, path.name)

    def test_upstream_modules_that_assume_uwsm_or_lock_are_not_loaded(self):
        text = (HYPR / "hyprland.lua").read_text()
        for module in ("default.hypr.omarchy", "default.hypr.autostart",
                       "default.hypr.bindings.utilities", "default.hypr.bindings.applications",
                       'require("default.hypr.qconsole")'):
            self.assertNotIn(module, text)

    def test_bound_omarchy_helpers_exist(self):
        text = (HYPR / "bindings.lua").read_text()
        helpers = set(re.findall(r'"(omarchy-[a-z0-9-]+)', text))
        helpers |= {"omarchy-toggle-" + name for name in
                    re.findall(r'toggle\("[^"]+", "[^"]+", "([a-z-]+)"', text)}
        helpers.discard("omarchy-toggle-")
        missing = sorted(h for h in helpers if not (RUNTIME / "bin" / h).is_file())
        self.assertEqual(missing, [])

    def test_only_super_ctrl_l_locks(self):
        text = (HYPR / "bindings.lua").read_text()
        self.assertEqual(text.count("omarchy-system-lock"), 1)
        self.assertIn('bind("SUPER + CTRL + L", "Lock system", "omarchy-system-lock")', text)
        self.assertNotIn("Lid Switch", text)

    @unittest.skipUnless(shutil.which("Hyprland"), "Hyprland is not installed")
    def test_hyprland_verifies_the_config(self):
        with tempfile.TemporaryDirectory() as home:
            home = Path(home)
            (home / ".config").mkdir()
            (home / ".local/share").mkdir(parents=True)
            (home / ".config/hypr").symlink_to(HYPR)
            (home / ".local/share/omarchy").symlink_to(RUNTIME)
            env = dict(os.environ, HOME=str(home), OMARCHY_PATH=str(RUNTIME))
            result = subprocess.run(
                ["Hyprland", "--verify-config", "-c", str(HYPR / "hyprland.lua")],
                env=env, capture_output=True, text=True, timeout=60)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output[-2000:])
            self.assertIn("config ok", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
