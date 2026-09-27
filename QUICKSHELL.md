# Quickshell port: source import and integration status

## Source and deployment

- Source checkout: `/home/thewaleed/thewaleed/omarchy`
- Upstream revision: `b679363bed05415771a1b1dc92c6899a908236f7`
- Upstream branch/version: `quattro`, `4.0.0.alpha`
- Stow directory: `~/dotfils`
- Stow package: `quickshell`
- Target: `$HOME`
- Runtime: `~/.local/share/omarchy`
- Shell layout: `~/.config/omarchy/shell.json`
- Entry point: `~/.local/bin/quickshell-desktop`

The source import includes the entire `shell/` and `bin/` trees, stock configuration templates, defaults, themes, application assets, branding, license, documentation, contributor guides, and tests. The original checkout remains the comparison baseline. Distribution installation scripts and migrations are not deployed.

The complete upstream bar layout is preserved: menu, workspaces, indicators, clock/calendar, keyboard layout, weather, updates, tray, agents, Bluetooth, network, audio, monitor, and power. Copying a feature's source does not mean its backing service or external application is installed or its Debian integration has been tested.

## Deployment commands

```sh
stow --simulate --verbose --dir="$HOME/dotfils" --target="$HOME" quickshell
stow --verbose --dir="$HOME/dotfils" --target="$HOME" quickshell
"$HOME/.local/bin/quickshell-desktop" check
```

Hyprland autostarts the bar through `~/.local/bin/quickshell-desktop start` (see *Hyprland session integration*). Use `quickshell-desktop restart` to restart it. The native lock and idle plugins are explicitly disabled in `shell.json` until Debian PAM/locking validation is completed; the Polkit agent is enabled and registers successfully.

`quickshell-desktop ipc ...` uses the same runtime root as the launcher. All Omarchy helpers are private to that launch environment rather than added to the global shell PATH. The entry point resolves the Stow-managed `shell.json` before Quickshell writes it atomically, preserving the deployment symlink when the UI saves settings.

## Initial Debian adaptations

| Area | Change | Validation status |
| --- | --- | --- |
| Runtime environment | Dedicated entry point establishes `OMARCHY_PATH` and the helper PATH without UWSM | Core/path check passed after Stow deployment |
| Settings persistence | Resolve the real Stow source before atomic `shell.json` updates | Isolated symlink-resolution test and deployed path check passed |
| Workspace clicks | Use the native Hyprland `workspace` dispatcher instead of compositor Lua | QML compilation passed; workspace indicators render in the live bar |
| App launcher | Use Quickshell's `DesktopEntry.execute()` instead of `uwsm-app` | Apps menu renders installed native and Flatpak entries; launch execution not automated |
| Update indicator | Read cached APT upgrade simulation, without automatic fetches | Availability/empty/error tests passed; actual cached query reported no upgrades |
| Update action | Open an interactive APT update/upgrade in Kitty | Explicit user action; not executed during setup |
| Restart | Wait for Quickshell 0.3.0 instances to exit and use a Hyprland `exec` dispatcher | Mocked lifecycle tests and actual live restarts passed |
| QML type discovery | Explicit local `qmldir` declarations for dynamically loaded types | Host and all plugin entry points compile on Quickshell 0.3.0 |
| Qt 6.8 notification syntax | Rename the reserved `transient` identifier to `isTransient` | Notification service compilation passed |
| Qt 6.8 host binding | Explicit host reference avoids the `shell: shell` self-binding | Binding-loop warning resolved in live runs |
| Package guards | Use dpkg package status/Provides and explicit name aliases | Tests distinguish installed, virtual, and removed packages |
| Physical network status | Inspect the main routing table rather than the WARP tunnel | Reports the actual Wi-Fi interface, SSID, signal, and gateway |
| DNS controls | Use NetworkManager's authorized API for the physical profile | Readback checked; mock tests cover target selection and invalid input; live DNS not changed for testing |
| Terminal/browser launch helpers | Kitty and GIO replace UWSM launch assumptions | Syntax checked; interactive launch coverage remains pending |
| Display controls | Native DPMS/monitor keywords replace Lua calls | Scale and brightness readback verified; scale changes persist in the owned fragment |
| Monitor persistence | Upstream behavior: the Display panel rewrites the scale in `~/.config/hypr/monitors.lua` | Mock test covers the `hl.monitor` eval and the file rewrite |
| Power profiles | Preserve current profile until a saved/user-selected preference exists | All available profiles and active state shown in the power panel |

## Verification completed

- GNU Stow 2.4.1 installed through APT.
- Conflict-free Stow deployment created four links; a repeated dry run is a no-op.
- Core runtime command/file checks pass through the deployed entry point.
- The bundled `omarchy` font is linked and discovered by fontconfig. Debian's `fonts-cascadia-code` includes the NF variants; it supplies the missing Nerd Font glyphs through APT. Icons were inspected in the live bar after installation.
- Ten shell integration tests cover the entry point, package/upgrade status semantics, DNS targeting, monitor persistence, restart behavior, and QML compilation. Four additional network-migration tests cover parsing and persistent rollback-service ownership.
- **41 shell/plugin entry points**, including the actual `shell.qml` host, compile using the installed Qt/Quickshell and Wayland backend. No plugin is instantiated by the probe: it opens no panels and starts no desktop services. HOME, state, cache, and Quickshell logs are isolated under a temporary directory; D-Bus addresses point to nonexistent test sockets.
- The original downloaded Omarchy checkout is still clean.
- Live screenshots were inspected for the bar, Apps menu, audio, network, display, power, and notifications. Both text and image clipboard watcher processes are running; private clipboard contents were not inspected.
- PipeWire, PipeWire-Pulse, and WirePlumber are active, with an analog sink and microphone source detected. No audible playback or Bluetooth pairing test was performed.
- Some non-fatal Qt 6.8 context/device-pixel-ratio warnings remain in startup logs and need investigation. They have not prevented the inspected core panels or notification popup from rendering.

Run the focused tests with:

```sh
python3 -B "$HOME/dotfils/tests/test_quickshell_port.py"
python3 -B "$HOME/dotfils/tests/test_network_migration.py"
python3 -B "$HOME/dotfils/tests/test_hypr_config.py"
python3 -B "$HOME/dotfils/tests/test_debian_menu.py"
```

The compilation test requires an available Wayland display socket and explicitly skips when there is none. Other tests use mocked external commands. Compilation, visual inspection, and service presence are distinct from validating every menu action.

## Desktop dependencies and network migration

The reproducible APT package list is in `packages/quickshell-desktop.txt`. This stage installed 57 initial packages, two XKB utility packages, and one Cascadia font package, without package removals or upgrades. PipeWire/WirePlumber and the XKB tools use trixie-backports to match the existing libraries.

Wi-Fi `wlp3s0` is now managed by NetworkManager using a root-private `Primary Wi-Fi` profile. WARP remains connected and owns its tunnel. The `network-manager` Stow package targets `/` and installs only the WARP exclusion drop-in:

```sh
sudo stow --simulate --verbose --dir="$HOME/dotfils" --target=/ network-manager
sudo stow --verbose --dir="$HOME/dotfils" --target=/ network-manager
```

Migration code is in `tools/migrate_wifi.py`. Credentials were transferred in memory to root-private NetworkManager files, never written into this dotfiles tree or command arguments. The original interfaces file, migration state, and a root-owned recovery script are retained under `/var/backups/quickshell-wifi`.

The first attempt failed because NetworkManager retained strict ifupdown ownership. Its rollback restored the configuration but initially ran recovery daemons inside the transient job, whose exit stopped those daemons. The retry corrected both issues: restart NetworkManager after removing legacy ownership, and use the persistent `networking.service` for recovery. A reboot and a user-side `managed=true` change occurred between attempts; that setting was preserved. The retry completed, verified DNS/outbound connectivity, and cancelled its rollback timer. Recovery also contains a persistent unmanaged-device drop-in for the legacy interface, if rollback is requested later.

Status and deliberate rollback commands:

```sh
sudo python3 -I /var/backups/quickshell-wifi/migrate_wifi.py status
# Only when intentionally reverting Wi-Fi management:
sudo python3 -I /var/backups/quickshell-wifi/migrate_wifi.py rollback
```

Unstowing the network-manager package removes only the WARP exclusion link; it does not undo the connection migration. Hyprland's autogenerated-config warning was cleared at runtime for preview, not by editing the original live configuration. It can return when that original configuration reloads.

## Hyprland session integration

Hyprland 0.55.2 reads `~/.config/hypr/hyprland.lua`. The previous `hyprland.conf` was the autogenerated stub, which caused the recurring warning banner. The `hypr` Stow package now owns `~/.config/hypr`:

```sh
stow --simulate --verbose --dir="$HOME/dotfils" --target="$HOME" hypr
stow --verbose --dir="$HOME/dotfils" --target="$HOME" hypr
Hyprland --verify-config
```

The stub and the unused `browser.conf` were moved to `~/.config/hypr.pre-stow-20260923-114420`. A running Hyprland keeps the config format it started with, so the Lua config takes effect at the next login.

`hyprland.lua` loads Omarchy's defaults from the imported runtime without editing them: envs, look and feel, input, window rules, the tiling/media/clipboard bindings, toggles, and the current theme when one exists. Personal overrides load after them:

| File | Purpose |
| --- | --- |
| `debian.lua` | `o.launch()` runs commands directly instead of through `uwsm-app` (UWSM is not installed) |
| `autostart.lua` | Exports the session environment, starts the bar via `quickshell-desktop start`, initializes the power profile |
| `bindings.lua` | Personal bindings merged with a curated Omarchy set (see below). Each command binding is set only if its program exists |
| `monitors.lua` | Startup scale 1.5 and GDK_SCALE 2; the Display panel rewrites these lines. The old nwg-displays HDMI mirror at scale 1.0 was not carried over |
| `input.lua` | From the previous config: `us,ara` layouts toggled with Alt+Shift, `follow_mouse = 1`, no natural scrolling |
| `looknfeel.lua` | From the previous config: `preserve_split`, no default wallpaper or logo. Appearance stays on Omarchy's flat defaults until the redesign |
| `screen-rotation.sh` | Previous accelerometer rotation script, now keeping the current scale. Autostarts only when `monitor-sensor` (package `iio-sensor-proxy`) is installed |

Not loaded from Omarchy: `autostart` (Arch provisioning, udiskie, UWSM monitor watch, post-boot hooks), `utilities`/`applications`/`voxtype` bindings (replaced by `bindings.lua`), and `qconsole` (needs the `workspace.special_active` event, which 0.55.2 lacks). Also omitted: the idle toggle, lid-switch lock, keybinding viewer (UWSM), agents/dictation, and webapps.

### Merge with the previous personal config

The previous config (`~/thewaleed/dotfiles/.config/hypr`, hyprlang format) was translated to Lua and merged. Conflicts were resolved as follows:

- **Personal window-management keys win:** SUPER+F float, SUPER+CTRL+F fullscreen, SUPER+T `hyprctl kill`, SUPER+K swap split, SUPER+SHIFT+arrows resize, SUPER+TAB `m±1`, SUPER+S / SHIFT+S scratchpad `magic` (Omarchy's scratchpad keys SUPER+grave and SUPER+ALT+S also target `magic`). This displaces Omarchy's fullscreen, tiled-fullscreen, float, and window-swap keys.
- **Keys whose app is not installed use the Omarchy equivalent:** SUPER+R and SUPER+CTRL+RETURN Apps menu (were waybar launcher/rofi), SUPER+V clipboard manager (was cliphist+rofi; replaces Omarchy's universal paste), PRINT / SHIFT+PRINT / CTRL+PRINT Omarchy region / window / full-screen screenshot (were hyprshot), SUPER+N notification history (was swaync), SUPER+period emojis (was gnome-characters). Media, volume, and brightness keys use the Omarchy helpers for the on-screen display.
- **Kept but inactive until installed:** SUPER+E thunar.
- **Not bound:** SUPER+L and XF86Lock (hyprlock is not installed; lock is checkpoint 1). Omarchy's SUPER+L workspace-layout toggle is cleared.
- **Autostart entries dropped:** waybar, swaync, cliphist, hyprpaper, hyprpolkitagent (covered by the Quickshell bar and its notifications, clipboard, background, and Polkit plugins), and autojump (a shell tool).
- **Environment dropped:** `XDG_MENU_PREFIX=arch-`, `QT_QPA_PLATFORMTHEME=qt6ct` (not installed), and the AMD GPU variables (the AMD chip has no display outputs; Hyprland renders on the Intel GPU). Cursor size 24 is already Omarchy's default.
- **`dwindle.pseudotile`** was removed in Hyprland 0.55; SUPER+P pseudo still works.

### Network share

The previous `sudo mount -t cifs ... password=...` autostart line was replaced by an on-demand systemd automount. The password is kept only in a root-only file, never in this tree:

```
//share.local/home  /mnt/share  cifs  credentials=/etc/samba/credentials/share,uid=1000,gid=1000,noauto,nofail,_netdev,x-systemd.automount,x-systemd.mount-timeout=10  0  0
```

`/etc/samba/credentials/share` (0600 root) holds `username=` and `password=` lines. Set the password with `sudo -e /etc/samba/credentials/share`. The original fstab is backed up as `/etc/fstab.bak-20260923-115501`.

Rollback:

```sh
stow --delete --dir="$HOME/dotfils" --target="$HOME" hypr
mv ~/.config/hypr.pre-stow-20260923-114420 ~/.config/hypr
```

## Omarchy menu on Debian

SUPER+SPACE opens Omarchy's menu. Upstream rows assume Arch, so a generated overlay adapts it:

- `quickshell/.config/omarchy/extensions/omarchy-menu.jsonc` is **generated** by `tools/generate-debian-menu.py`. Edit the script or the catalog, then re-run it. The shell's overlay parser fills omitted fields with defaults, so the generator restates each overridden upstream row in full.
- `default/omarchy/debian-apps.conf` is the Install/Remove catalog. Each app comes from APT, a vendor `.deb` (Chrome, Edge, VS Code), a vendor APT repo (Sublime, 1Password, Signal, Tailscale, NordVPN; key and list paths follow each vendor's instructions), Flathub (per-user), or a custom step (Docker, Rust, Laravel, Phoenix). `omarchy-debian-app install|remove|present|list <id>` runs them. Install rows dim with ✓ once installed; Remove rows show only what is installed. Install/Remove also offer apt and Flatpak pickers (fzf).
- Hidden: Learn, AUR, Windows VM, Preinstalls, release channels, Reset Computer, Direct Boot, Plymouth, hybrid GPU, crash capture, Stay Awake (checkpoint 1; the idle service only locks), Config > XCompose (fcitx5 not installed), Passwordless Sudo (sudo is already passwordless via `/etc/sudoers.d/99-thewaleed`), fingerprint (no reader), Drive Encryption (no LUKS), apps without a Debian source (Zig, Bun, Deno, .NET, Scala, Symfony, Cursor, Helix, Ghostty, Brave Origin, most AI apps), and **Update > Config > Hyprland/Shell**, which would overwrite the Stow-managed `~/.config/hypr` and `shell.json`.
- Update > System (and the bar's update icon) runs `omarchy-debian-update`: APT `full-upgrade` with its confirmation, then Flatpak updates.
- Default Agent lists only agents already installed (upstream installs them with mise, which Debian lacks).

Debian fixes behind the menu:

| Problem | Fix |
| --- | --- |
| Shell ran guards and actions with `bash -lc`; Debian's `/etc/profile` resets PATH and drops the private helpers, so most rows failed | Shell QML and `omarchy-theme-set` use `bash -c`, inheriting the session PATH |
| Under the Lua config, `hyprctl keyword` and legacy `hyprctl dispatch exec/exit/dpms` are ignored while exiting 0 | Restart, logout, brightness, scaling, and screen rotation use `hl.*` forms; scaling persists into `hypr/monitors.lua` (upstream behavior); the old `~/.config/omarchy/monitors.conf` was removed |
| UWSM not installed | `uwsm-app` shim in the private bin runs the command directly |
| Debian's `xdg-terminal-exec` 0.12 opens a terminal for unknown flags such as `--print-id` | Wrapper answers `--print-id` from `~/.config/xdg-terminals.list` (kitty) |
| pacman-based package helpers | `omarchy-pkg-add/drop/install/remove` use APT with an Arch-to-Debian name map; `omarchy-pkg-list` also lists Flatpak app ids |
| gpu-screen-recorder not packaged | Screen recording uses `wf-recorder`; desktop+microphone are mixed through a temporary PulseAudio null sink; webcam overlay dropped |
| tensaku-edit not packaged | `swappy` edits screenshots and clipboard images |
| Nerd Font packages | Fonts install from the official Nerd Fonts release into `~/.local/share/fonts` |
| Browser theming writes root-owned policies via missing install helpers | Skipped; the rest of a theme applies |
| FIDO2 setup would replace Debian's vendor `polkit-1` PAM file with a bare one | Copies `/usr/lib/pam.d/polkit-1` to `/etc` and adds the FIDO2 line |
| SSHD / firmware | `ssh.service`; fwupd without the Arch EFI copy |
| Trigger > Transcode silently did nothing: `omarchy-menu-file` aborted on the missing `~/Videos` before showing the picker | The picker skips missing search paths and fails only when none exist |
| The session PATH lacked `/usr/sbin`, so `rfkill`/`iw` were missing: Update > Hardware > Wi-Fi/Bluetooth failed and Wi-Fi status showed the profile name instead of the SSID | `quickshell-desktop` appends `/usr/local/sbin:/usr/sbin:/sbin` |
| Apps: `DesktopEntry.execute()` ignores `Terminal=true`, so Neovim, Vim, ranger, fish, and Python opened no window | `AppLibrary.launch()` runs terminal entries through `xdg-terminal-exec` |
| Apps: Delete (uninstall) looked up the owner with `pacman -Qqo` | `omarchy-remove-launcher-entry` uses `dpkg-query -S` and `sudo apt remove` (Flatpak branch unchanged) |
| Trigger > Screenrecord failed: `~/Videos` does not exist on this install | The recorder creates its output directory, like the screenshot helper |
| Trigger > Share called `localsend --headless send`; the LocalSend .deb ships only the GUI `localsend_app` | Share opens `localsend_app` with the files |
| Style > About: no `~/.config/omarchy/branding/about.txt`, and Omarchy's fastfetch config was not deployed (stock Debian output) | `about.txt` seeded from `icon.txt`; the `fastfetch` Stow package (target `/`) installs `/etc/fastfetch/config.jsonc` with the OS line from `/etc/os-release`, no Arch branch/channel lines, and `printf` instead of dash's `echo -e`; `omarchy-version-pkgs` reads the APT history log |
| Setup > Security > Sudoless Docker showed without Docker | Guarded on `docker` being installed |
| Setup > Plugins > Clone needs `rg` | `ripgrep` installed and added to the package list |
| System > Hibernate was always hidden: the check wanted Arch's mkinitcpio resume file | Also accepts Debian's `/etc/initramfs-tools/conf.d/resume` (swap `/dev/sda7`) |
| System > Lock was hidden and no key locked: `omarchy.lock` was off and `/etc/pam.d/omarchy-lock-password` was never written (upstream's file includes Arch's `system-local-login`) | The Lock Screen Explorer plugin replaces `omarchy.lock`; the PAM file includes Debian's `common-auth`/`common-account`; System > Lock is shown and SUPER+CTRL+L locks |
| Style > Theme/Background: 80 of 91 theme backgrounds are `.webp`, which Qt could not decode without `qt6-image-formats-plugins`, so the wallpaper stayed blank. The background picker was empty: `vipsthumbnail` was missing, and Debian's libvips 8.16 lacks upstream's `--path` option | Installed `qt6-image-formats-plugins`, `libvips-tools`, and `ffmpegthumbnailer` (package list); `omarchy-menu-images` uses `-o`, and its test stub accepts both |

The Tokyo Night theme (Omarchy's first-run default) was applied. Fira Code Nerd Font was installed while testing the font installer.

Not yet exercised end to end: catalog installs that need `sudo` (the menu's terminal prompts for the password), Flatpak installs, and the security setup flows.

## Agents panel providers

Tabs are named after the provider whose usage they count: **Anthropic** (Claude Code) and **OpenAI** (Codex CLI plus OpenCode/pi sessions on OpenAI models); the collectors' `AGENT_NAME` was changed. Debian adds `omarchy-debian-router-usage` with `omarchy-agent-usage-openrouter` and `-orcarouter`: local stats from OpenCode's database and saved pi sessions, and the live balance from the provider API using the key OpenCode already stores (OpenRouter `/credits`; OrcaRouter's OpenAI-shape billing endpoints, where an unlimited key shows no balance). A provider tab appears only once it has usage. Icons are in `plugins/agents/assets/<id>.svg`.

The Agents panel header has an **Open Herdr** button (`omarchy-launch-terminal-herdr`). Herdr 0.9.1 is installed in `~/.local/bin` by its official checksum-verified installer (catalog id `ai.herdr`; update with `herdr update`); the `herdr` Stow package links Omarchy's config (prefix Ctrl+Space). Switching tabs forces a layout pass (`relayoutColumns`), because Qt 6.8's Column otherwise kept the previous tab's height.

The pi coding agent was uninstalled (npm). `~/.pi` was left in place: it holds pi's sessions and credentials and an unrelated SSH key.

## Workspaces

The bar shows workspaces 1–4 always, plus any higher workspace while it exists, up to 9 (`alwaysShow`/`maximum` settings on the `omarchy.workspaces` entry in `shell.json` override this). SUPER+0 (workspace 10) is unbound in `hypr/bindings.lua` to match.

## Display panel

The bar's Display panel (`omarchy.monitor`) handles brightness, scale and which displays are on. [hyprmoncfg](https://github.com/crmne/omarchy-hyprmoncfg) layouts were removed on 2026-09-27 (plugin, `hyprmoncfg` .deb, `hyprmoncfgd`, saved profiles, and its rules in `hypr/`). `panels/monitor/Panel.qml` still adds a LAYOUTS section if the plugin reappears at `~/.config/omarchy/plugins/crmne.hyprmoncfg`, and hides it otherwise. If you reinstall it, `hyprmoncfg manage` puts a load line at the end of `hypr/hyprland.lua` that wins over `hypr/monitors.lua`.

## Apps

Installed through the catalog: Nautilus (default for folders; SUPER+E, SUPER+SHIFT+F), Mousepad (default for text files), Neovim, Hermes Agent (`uv tool`), Herdr. Antigravity IDE 2.x ships only as a tarball (Google's APT repo stops at 1.23.2), so it lives in `/opt/antigravity-ide`; to update, download "Antigravity IDE.tar.gz" from antigravity.google/download and copy it over that folder. The `apps` Stow package (`--no-folding`) holds its launcher, menu entries and icon, which run it with `--user-data-dir=~/.config/Antigravity-IDE` (the folder the 1.x install used, so settings and sign-in carry over). Extensions live in `~/.antigravity-ide/extensions`.

`omarchy-sudo-keepalive` now skips `sudo -v` when `sudo -n true` works: with the NOPASSWD rule in `/etc/sudoers.d/99-thewaleed`, `sudo -v` still demanded a password and aborted catalog installs.

## Remaining full-feature integration checkpoints

1. **Lock/idle activation:** `omarchy.lock` and `omarchy.idle` are temporarily disabled, pending Debian PAM/session integration and user-assisted authentication validation.
2. **Audio/media:** service/device discovery and the panel are working; test audible playback, recording, output changes, per-app volume, and media actions as appropriate.
3. **Networking:** migration and WARP coexistence are verified. Wi-Fi QR/password presentation and live DNS/profile changes remain separate interaction checks.
4. **Bluetooth/power/brightness:** power/brightness state and panels are verified; Bluetooth pairing requires a device and a reviewed pairing-agent policy.
5. **Menus and helpers:** the menu is ported (see *Omarchy menu on Debian*). Helpers not reachable from the menu may still assume Arch.
6. **Clipboard, capture, reminders, weather, agents:** verify their package dependencies, state handling, network/provider settings, and CLI integrations. Keep all imported features accounted for rather than silently dropping widgets.
7. **Fonts:** Nerd Font coverage is supplied through APT; final typography belongs to the redesign.
8. **Session integration:** done at the config level (see above). Pending: confirm autostart and bindings after the next login, and port the omitted bindings as their helpers become Debian-ready.
9. **Functional and visual checks:** extend interaction coverage and investigate remaining Qt warnings. Do not run the repository's graphical acceptance suite on the main session; its guide requires a disposable VM.
10. **Redesign after functionality:** dark/crisp appearance, top bar and unified control center, keyboard/mouse first. The running interface still uses Omarchy's stock layout and panels.

## Undo deployment

```sh
stow --delete --verbose --dir="$HOME/dotfils" --target="$HOME" quickshell
```

This removes managed links, not the source tree. Generated runtime state and installed APT packages are separate from Stow.
