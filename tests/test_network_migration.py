import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import tempfile

spec = importlib.util.spec_from_file_location("migration", Path(__file__).resolve().parents[1] / "tools/migrate_wifi.py")
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


class ParserTests(unittest.TestCase):
    def test_preserves_other_interfaces_and_removes_only_wifi_credentials(self):
        text = ('source /etc/network/interfaces.d/*\nauto lo\niface lo inet loopback\n'
                'allow-hotplug wlp3s0 enp2s0\niface wlp3s0 inet dhcp\n'
                '  wpa-ssid "Example network"\n  wpa-psk "example-password"\n'
                'iface enp2s0 inet dhcp\n')
        ssid, psk, remaining = migration.parse_interfaces(text, "wlp3s0")
        self.assertEqual(ssid, "Example network")
        self.assertEqual(psk, "example-password")
        self.assertIn("allow-hotplug enp2s0", remaining)
        self.assertIn("iface enp2s0 inet dhcp", remaining)
        self.assertIn("iface lo inet loopback", remaining)
        self.assertNotIn("wpa-", remaining)
        self.assertNotIn("wlp3s0", remaining)

    def test_refuses_unhandled_options(self):
        text = ('iface wlp3s0 inet dhcp\n wpa-ssid Example\n wpa-psk example-password\n'
                ' post-up custom-routing-command\n')
        with self.assertRaisesRegex(ValueError, "manual review"):
            migration.parse_interfaces(text, "wlp3s0")

    def test_accepts_hashed_psk_without_changing_it(self):
        digest = "a1" * 32
        text = f"iface wlp3s0 inet dhcp\n wpa-ssid Example\n wpa-psk {digest}\n"
        self.assertEqual(migration.parse_interfaces(text, "wlp3s0")[1], digest)

    def test_rollback_uses_persistent_networking_service(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "interfaces.original").write_text("auto lo\niface lo inet loopback\n")
            (root / "interfaces.networkmanager").write_text("auto lo\niface lo inet loopback\n")
            (root / "interfaces").write_text("auto lo\niface lo inet loopback\n")
            state = {"interface": "wlp3s0", "uuid": "test-uuid", "keyfile": "test.nmconnection"}
            with patch.object(migration, "BACKUP", root), \
                 patch.object(migration, "INTERFACES", root / "interfaces"), \
                 patch.object(migration, "CONNECTIONS", root), \
                 patch.object(migration, "RECOVERY_CONF", root / "recovery.conf"), \
                 patch.object(migration, "run") as runner:
                migration.rollback(state)
            calls = [call.args for call in runner.call_args_list]
            self.assertIn(("systemctl", "restart", "networking.service"), calls)
            self.assertFalse(any(call[0] == "ifup" for call in calls))
            self.assertEqual(state["status"], "rolled-back")
            self.assertIn("managed=0", (root / "recovery.conf").read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
