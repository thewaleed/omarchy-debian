# Personal desktop dotfiles

GNU Stow source directory: `~/dotfils`. Target directory: `$HOME`.

## Clone

Three Omarchy themes/plugins (`cpunk`, `aetheria`, `lock-explorer`) are git submodules:

```sh
git clone --recurse-submodules git@github.com:thewaleed/omarch-debian.git ~/dotfils
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

## Other home packages

These packages target `$HOME`:

- `apps`: Antigravity launcher and `.desktop` entries
- `fish`: `config.fish` and `conf.d/ssh-agent.fish`
- `herdr`: herdr `config.toml`
- `kitty`: `kitty.conf` and its pywal template
- `desktop`: chrome flags, `environment.d`, `mimeapps.list`, `xdg-terminals.list`, the LocalSend autostart entry, GTK bookmarks
- `systemd`: the `wayvnc-keepalive-check` user service and timer. After stowing, run `systemctl --user enable --now wayvnc-keepalive-check.timer`.
- `shell`: `.bashrc` and `.profile`
- `git`: `.gitconfig`

```sh
stow --verbose --dir="$HOME/dotfils" --target="$HOME" apps fish herdr kitty desktop systemd shell git
```
