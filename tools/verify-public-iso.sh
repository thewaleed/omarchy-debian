#!/bin/bash
# Check a public eggs ISO for personal data before sharing it.
#
#   sudo tools/verify-public-iso.sh /home/eggs/egg-of-....iso
#
# Collects the real secrets on THIS machine (Wi-Fi SSIDs and passwords, the
# Cloudflare tunnel token, Samba credentials, account names, email) and greps
# the ISO's filesystem for them as fixed strings, binary files included.
# Exits non-zero and lists the files if anything turns up.
set -euo pipefail

ISO=${1:?usage: verify-public-iso.sh ISO}
[ "$(id -u)" = 0 ] || { echo "run as root (reads secrets and mounts the ISO)" >&2; exit 1; }

WORK=$(mktemp -d)
chmod 700 "$WORK"
cleanup() {
    umount "$WORK/sq" 2>/dev/null || true
    umount "$WORK/iso" 2>/dev/null || true
    rm -rf "$WORK"
}
trap cleanup EXIT
mkdir "$WORK/iso" "$WORK/sq"
mount -o loop,ro "$ISO" "$WORK/iso"
mount -o loop,ro "$WORK/iso/live/filesystem.squashfs" "$WORK/sq"
R=$WORK/sq
fail=0

# --- needles: secrets as they exist on this machine ------------------------
NEEDLES=$WORK/needles
{
    for f in /etc/NetworkManager/system-connections/*.nmconnection; do
        [ -f "$f" ] && sed -nE 's/^(ssid|psk|password|wep-key0)=(.+)$/\2/p' "$f"
    done
    [ -f /etc/cloudflared/token ] && cat /etc/cloudflared/token
    for f in /etc/samba/credentials/*; do
        [ -f "$f" ] && sed -nE 's/^(username|password)=(.+)$/\2/p' "$f"
    done
    awk -F: '$3 >= 1000 && $3 < 60000 && $1 != "live" {print $1}' /etc/passwd
    [ -n "${SUDO_USER:-}" ] && sudo -u "$SUDO_USER" git config --global user.email 2>/dev/null
    true  # a false [ ] test above must not fail the pipeline under pipefail
} | awk 'length($0) >= 5' | sort -u > "$NEEDLES"
echo "checking for $(wc -l < "$NEEDLES") secrets/identifiers from this machine"

# A common password can also occur in vendor files by coincidence. Ignore a hit
# when the file is byte-identical to what its package shipped (per the ISO's
# own dpkg records), or when it's listed in the allowlist next to this script.
ALLOW=$(dirname "$0")/verify-public-iso.allow
is_vendor() {
    local p=$1 sum
    [ -f "$ALLOW" ] && grep -v '^#' "$ALLOW" | grep -qxF "$p" && return 0
    sum=$(md5sum < "$R$p" | cut -d' ' -f1)
    grep -qxF "$sum  ${p#/}" "$R"/var/lib/dpkg/info/*.md5sums 2>/dev/null && return 0
    grep -qxF " $p $sum" "$R/var/lib/dpkg/status" 2>/dev/null
}
hits=""
while IFS= read -r p; do
    is_vendor "$p" || hits+="$p"$'\n'
done < <(grep -rlaF -f "$NEEDLES" "$R/etc" "$R/var" "$R/home" "$R/usr/local" "$R/opt" "$R/srv" 2>/dev/null \
    | sed "s|^$R||" || true)
hits=${hits%$'\n'}
if [ -n "$hits" ]; then
    echo "FAIL: files containing personal data:"; sed 's/^/  /' <<<"$hits"; fail=1
fi

# --- files that must not exist ---------------------------------------------
bad=$(cd "$R" && find etc var usr/local root home \( \
    -name '*.nmconnection' -o -name 'ssh_host_*_key' -o -path 'etc/cloudflared*' \
    -o -name 'shadow-' -o -name 'passwd-' -o -path 'var/lib/plocate/*' \
    -o -path 'var/lib/tor/keys*' -o -path 'etc/samba/credentials/*' \
    -o -path 'var/lib/systemd/linger/*' \) -print 2>/dev/null || true)
if [ -n "$bad" ]; then
    echo "FAIL: files that should have been excluded:"; sed 's/^/  /' <<<"$bad"; fail=1
fi

# --- accounts: only the live user may have a login -------------------------
users=$(awk -F: '$3 >= 1000 && $3 < 60000 {print $1}' "$R/etc/passwd")
if [ "$users" != live ]; then
    echo "FAIL: unexpected user accounts: $users"; fail=1
fi
hashes=$(awk -F: '$2 ~ /^\$/ && $1 != "live" {print $1}' "$R/etc/shadow")
if [ -n "$hashes" ]; then
    echo "FAIL: password hashes for: $hashes"; fail=1
fi
homes=$(ls "$R/home")
if [ "$homes" != live ]; then
    echo "FAIL: unexpected home dirs: $homes"; fail=1
fi

if ((fail)); then echo "NOT SAFE TO SHARE"; exit 1; fi
echo "PASS: no personal data found in $(basename "$ISO")"
