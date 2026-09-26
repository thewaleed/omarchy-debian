# Personal desktop dotfiles

GNU Stow source directory: `~/dotfils`. Target directory: `$HOME`.

## Clone

Four Omarchy themes/plugins (`cpunk`, `aetheria`, `lock-explorer`, `hyprmoncfg`) are git submodules:

```sh
git clone --recurse-submodules git@github.com:thewaleed/omarchy-debian.git ~/dotfils
```

## Quickshell

The `quickshell` package contains the locally downloaded Omarchy shell, its complete bar/plugin sources, and supporting runtime assets. Debian integration is being added before the visual redesign.

Check links before applying them:

```sh
stow --simulate --verbose --dir="$HOME/dotfils" --target="$HOME" quickshell
stow --verbose --dir="$HOME/dotfils" --target="$HOME" quickshell
```

Remove the managed links with:

```sh
stow --delete --verbose --dir="$HOME/dotfils" --target="$HOME" quickshell
```

Do not use `--adopt`: existing destination files must be reviewed rather than moved into this source tree automatically.

Source provenance and integration status are documented in `QUICKSHELL.md`.

The stock bar autostarts from Hyprland while its Debian port is completed. The APT dependency manifest is `packages/quickshell-desktop.txt`; focused tests are under `tests/`.

## Hyprland

The `hypr` package owns `~/.config/hypr` (Hyprland 0.55 Lua config) and autostarts the bar:

```sh
stow --verbose --dir="$HOME/dotfils" --target="$HOME" hypr
```

Details and rollback are in `QUICKSHELL.md`.

## NetworkManager

The `network-manager` package targets `/`, not `$HOME`, and contains the NetworkManager drop-in that leaves the WARP tunnel unmanaged:

```sh
sudo stow --simulate --verbose --dir="$HOME/dotfils" --target=/ network-manager
sudo stow --verbose --dir="$HOME/dotfils" --target=/ network-manager
```

Wi-Fi credentials and migration backups are root-private and intentionally outside this source tree. Migration and rollback details are in `QUICKSHELL.md`.

## Fastfetch

The `fastfetch` package also targets `/`. It installs the Debian version of Omarchy's `/etc/fastfetch/config.jsonc`, which the About window (Omarchy menu › About) renders:

```sh
sudo stow --simulate --verbose --dir="$HOME/dotfils" --target=/ fastfetch
sudo stow --verbose --dir="$HOME/dotfils" --target=/ fastfetch
```

## udev

The `udev` package holds `60-uinput-uaccess.rules`, which lets the logged-in user open `/dev/uinput` so the `ydotool` user service can start. It uses `uaccess` rather than the `input` group, which would also expose every keyboard's raw events. Install it as a copy, not with stow: udev reads rules before `/home` is mounted, so a symlink into this repo would be skipped at boot.

```sh
sudo install -m 644 udev/etc/udev/rules.d/60-uinput-uaccess.rules /etc/udev/rules.d/
sudo udevadm control --reload && sudo udevadm trigger --action=change --sysname-match=uinput
systemctl --user reset-failed ydotool && systemctl --user restart ydotool
```

## Remote Herdr access

- **Phone:** Herdr Mobile Relay plugin (`herdr plugin install 0cv/herdr-mobile-relay`), stable tunnel `relay-debian.thewaleed.me`, managed by the plugin wizard (`herdr-mobile-relay.service`). Reprint the pairing QR with `herdr plugin action invoke setup-link --plugin herdr-mobile-relay.events`.
- **Office browser:** `term.thewaleed.me` → `herdr-term-tunnel` (cloudflared) → `herdr-term-caddy` (password) → `herdr-ttyd` → `herdr`. The Caddyfile lives in the `herdr` package; the user units in `systemd`.
- **Office desktop:** `term.thewaleed.me/desktop/` (same password) → `herdr-term-desktop` (websockify + noVNC from `sudo apt install novnc`) → wayvnc on `127.0.0.1:5900`. Works only while a Hyprland session is logged in, since wayvnc starts from Hyprland autostart.

Machine-local pieces that are not tracked:

- `~/.local/bin/ttyd`: static binary from the tsl0922/ttyd GitHub release, checked against its `SHA256SUMS`
- `~/.local/state/herdr-term/secret.env` (mode 600): `HERDR_TERM_USER=…` and `HERDR_TERM_HASH=…` from `caddy hash-password`
- `~/.cloudflared/config-herdr-term.yml` and the tunnel credentials JSON from `cloudflared tunnel create herdr-term`

```sh
systemctl --user enable --now herdr-ttyd herdr-term-desktop herdr-term-caddy herdr-term-tunnel
systemctl --user stop herdr-term-tunnel   # cut office access immediately
```

The office page is a full shell behind one password: keep it long and never save it in the office browser.

## Other home packages

These packages target `$HOME`:

- `apps`: Antigravity launcher and `.desktop` entries
- `fish`: `config.fish` and `conf.d/ssh-agent.fish`
- `herdr`: herdr `config.toml` and the `herdr-term` Caddyfile
- `kitty`: `kitty.conf`, its pywal template, and `~/.local/bin/wal-sync` (regenerates colors from the Omarchy background; autostarted by Hyprland)
- `desktop`: chrome flags, `environment.d`, `mimeapps.list`, `xdg-terminals.list`, the LocalSend autostart entry, GTK bookmarks
- `systemd`: the `wayvnc-keepalive-check` user service and timer, plus the `herdr-*` remote-access units (see above). After stowing, run `systemctl --user enable --now wayvnc-keepalive-check.timer`.
- `wayvnc`: `~/.local/bin/wayvnc-keepalive` (autostarted by Hyprland) and `wayvnc-keepalive-check` (run by the `systemd` timer)
- `gh`: GitHub CLI `config.yml` (`hosts.yml` holds the auth token and is intentionally not tracked)
- `shell`: `.bashrc` and `.profile`
- `git`: `.gitconfig`

```sh
stow --verbose --dir="$HOME/dotfils" --target="$HOME" apps fish herdr kitty wayvnc gh desktop systemd shell git
```
