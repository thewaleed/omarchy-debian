# Update process (Debian port)

Debian owns the system packages here, so there is no Omarchy package channel, no pacman pipeline, no Snapper snapshot and no migration runner. An update is an explicit user action that runs APT and Flatpak in a visible terminal.

## Entry points

- The bar's update icon (`shell/plugins/bar/widgets/SystemUpdate.qml`) and the Update > System menu row run `omarchy-debian-update`.
- `omarchy update` (`bin/omarchy-update`) is a compatibility shim that execs `omarchy-debian-update`.

## What `omarchy-debian-update` does

Inside `omarchy-launch-floating-terminal-with-presentation`:

1. `sudo apt update && sudo apt full-upgrade`, keeping APT's own transaction confirmation.
2. After a successful upgrade: `omarchy-update-pkg-prune` (`apt-get autoclean`) and `omarchy-update-orphan-pkgs` (lists what `apt-get autoremove` would remove and asks with `gum confirm` before removing it; outside a terminal it only reports).
3. `flatpak update` when Flatpak is installed.
4. `omarchy-shell -q omarchy.system-update refresh` so the bar indicator reflects the new state.

The exit status is the APT or Flatpak failure, if any.

## Update indicator

`omarchy-update-available` inspects the cached APT database with `apt-get --simulate upgrade`. It never refreshes package lists or contacts a mirror, so the bar can poll it (every 6 hours) cheaply. It keeps the upstream contract: exit 0 when updates are available, 1 when there are none, 2 when the check failed. `omarchy-update-status` refreshes or clears the indicator from the same check.

## After an update

`omarchy-update-restart` offers a reboot when the newest `/boot/vmlinuz-*` is newer than the running kernel, when `/run/reboot-required` or `~/.local/state/omarchy/reboot-required` exists, or when the running Hyprland binary was replaced. It then restarts any component flagged with `~/.local/state/omarchy/restart-<name>-required` and the shell. Setup > Security > Sudoless Docker uses it after changing group membership.
