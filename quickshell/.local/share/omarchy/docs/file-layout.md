# File layout (Debian port)

How this Omarchy runtime is organized on the Debian machine. There are no Arch packages: the tree lives in the `~/dotfils` repository and GNU Stow links it into place.

## Mental model

- Source: `~/dotfils/quickshell/.local/share/omarchy`, stowed to `~/.local/share/omarchy`. That path is `$OMARCHY_PATH`; `hypr/.config/hypr/hyprland.lua` exports it to the session.
- `bin/` is not on the login PATH. `~/.local/bin/quickshell-desktop` prepends `$OMARCHY_PATH/bin` for the shell and everything it launches, which is why Hyprland bindings check helpers by full path.
- Hyprland reads the user config in `~/dotfils/hypr/.config/hypr/`. It loads selected modules from `default/hypr/` (helpers, envs, look and feel, input, windows, tiling/media/clipboard/voxtype bindings, toggles) and its own `autostart.lua`. Upstream's `default/hypr/omarchy.lua` and `default/hypr/autostart.lua` are not loaded.
- Debian packages, Flatpaks and vendor APT repositories replace Omarchy's Arch package set. Everything the Install and Remove menus offer comes from the catalog below.

## Directories

| Path | Contents |
| --- | --- |
| `bin/` | `omarchy-*` commands, routed by `bin/omarchy` (`GROUP_DESCRIPTIONS` lists the groups) |
| `shell/` | The Quickshell desktop (bar, menu, notifications, OSD, services) |
| `default/` | Shipped defaults read in place: Hyprland modules, menu definition, app catalog, themed templates, systemd user units, agent skills |
| `config/` | Templates that `omarchy-refresh-config` copies into `~/.config/` |
| `themes/` | Stock themes |
| `applications/` | Desktop entries and icons for Omarchy launchers |
| `agents/`, `docs/` | Contributor guides and reference docs |
| `test/` | Upstream CLI and shell tests (`./test/cli`, `./test/shell`); Debian-specific tests live in `~/dotfils/tests/` |

## Debian-specific pieces

- `default/omarchy/debian-apps.conf` — the app catalog (`id|label|method|packages|source`, methods `apt`, `deb`, `repo`, `flatpak`, `custom`).
- `bin/omarchy-debian-app` — installs, removes and checks catalog apps; vendor repositories and custom installers live here.
- `tools/generate-debian-menu.py` (in `~/dotfils`) — writes the menu overlay `quickshell/.config/omarchy/extensions/omarchy-menu.jsonc` from the vendored `default/omarchy/omarchy-menu.jsonc` and the catalog. It fails if an Install/Remove row has no catalog source: rows that cannot work on Debian are deleted from the vendored menu, never hidden.
- `bin/omarchy-debian-update` — the update flow; see `docs/update-process.md`.

## Quick reference: where does X live?

| Goal | Touch |
| --- | --- |
| Default file at `~/.config/foo/` | `config/foo/` |
| App offered in Install/Remove | a line in `default/omarchy/debian-apps.conf`, then re-run `tools/generate-debian-menu.py` |
| Menu row | `default/omarchy/omarchy-menu.jsonc`, then re-run the generator |
| User-facing `omarchy-*` command | `bin/omarchy-<group>-<verb>` — see `GROUP_DESCRIPTIONS` in `bin/omarchy` |
| Hyprland binding or autostart | `~/dotfils/hypr/.config/hypr/` |
| New stock theme | `themes/<name>/` (+ matching templates under `default/themed/` if they need theme colors) |
| User-installed theme | `~/.config/omarchy/themes/<name>/` |
| Generated current theme/background state | `~/.local/state/omarchy/current/` |
