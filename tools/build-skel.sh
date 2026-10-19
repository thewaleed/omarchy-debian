#!/bin/bash
# Build a shareable /etc/skel from these dotfiles, for the public eggs ISO.
#
# Copies the desktop stow packages with symlinks resolved (so nothing points
# back into ~/dotfils or /home/thewaleed), scrubs personal bits, and refuses
# to install if any personal reference survives.
#
#   tools/build-skel.sh            # stage and check only
#   tools/build-skel.sh --install  # also replace /etc/skel (backup: /etc/skel.orig)
set -euo pipefail

DOTFILES=$(cd "$(dirname "$0")/.." && pwd)

# Stow packages that make up the desktop's look and feel. Left out on purpose:
# git (name/email), gh (token), herdr, network-manager, wayvnc and systemd
# (tunnel/remote-desktop units), apps (Antigravity launcher), fastfetch (/etc).
PACKAGES=(hypr kitty fish quickshell desktop shell)
# Home paths outside the stow tree that are part of the look. Only current/
# from omarchy's state: the rest of it is clipboard history and notifications.
EXTRA=(.config/wal .config/gtk-4.0 .config/mpv .local/state/omarchy/current)
PERSONAL='thewaleed|@live\.com|rabii|inwi'

STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

# Start from Debian's stock skel so .bash_logout etc. survive a re-run.
SKEL_BASE=/etc/skel
[ -d /etc/skel.orig ] && SKEL_BASE=/etc/skel.orig
cp -a "$SKEL_BASE/." "$STAGE/"

copy() {
    rsync -r --copy-links --exclude=.git --exclude=__pycache__ \
        --exclude='*.bak' --exclude='*.bak[0-9]*' "$1" "$2"
}
for pkg in "${PACKAGES[@]}"; do
    copy "$DOTFILES/$pkg/" "$STAGE/"
done
for path in "${EXTRA[@]}"; do
    [ -e "$HOME/$path" ] || continue
    mkdir -p "$STAGE/$(dirname "$path")"
    copy "$HOME/$path" "$STAGE/$(dirname "$path")/"
done

# --- scrub ---------------------------------------------------------------
# Remote desktop over the Cloudflare tunnel is personal infrastructure.
sed -i '/VNC server for remote desktop/,+1d' "$STAGE/.config/hypr/autostart.lua"
sed -i '1s|, merged from .*keybindings.conf|, merged from the original keybindings.conf|' \
    "$STAGE/.config/hypr/bindings.lua"
sed -i 's|/home/thewaleed/|$HOME/|g' "$STAGE/.bashrc"
sed -i 's|traced from ~/thewaleed/[^ )]*|traced from a photo|' \
    "$STAGE/.local/share/omarchy/shell/plugins/menu/BarWidget.qml"
sed -i 's|via /etc/sudoers.d/99-thewaleed|on the author'"'"'s machine|' \
    "$STAGE/.config/omarchy/extensions/omarchy-menu.jsonc"
# Bookmarks point at the author's Windows partition.
rm -f "$STAGE/.config/nautilus/nautilus-bookmarks"

# No display manager: new users log in on tty1 and land straight in Hyprland.
cat >> "$STAGE/.profile" <<'EOF'

# Start Hyprland after logging in on the first console (no display manager).
if [ -z "${WAYLAND_DISPLAY:-}" ] && [ "$(tty)" = /dev/tty1 ] && command -v start-hyprland >/dev/null; then
    exec start-hyprland
fi
EOF

# --- checks --------------------------------------------------------------
if leaks=$(grep -rIlE "$PERSONAL" "$STAGE"); then
    echo "personal references left in skel:" >&2
    sed "s|^$STAGE/|  |" <<<"$leaks" >&2
    exit 1
fi
if links=$(find "$STAGE" -type l); [ -n "$links" ]; then
    echo "unexpected symlinks left in skel:" >&2
    echo "$links" >&2
    exit 1
fi
echo "staged skel: $(du -sh "$STAGE" | cut -f1), $(find "$STAGE" -type f | wc -l) files, no personal refs"

if [ "${1:-}" = --install ]; then
    [ -d /etc/skel.orig ] || sudo cp -a /etc/skel /etc/skel.orig
    sudo rsync -a --delete --chown=root:root "$STAGE/" /etc/skel/
    sudo chmod -R u+rwX,go+rX,go-w /etc/skel
    echo "installed into /etc/skel (stock copy kept at /etc/skel.orig)"
fi
