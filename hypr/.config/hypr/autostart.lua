-- Session autostart. Omarchy's own autostart module is not loaded: it starts
-- the shell without the Debian launcher and runs Arch provisioning hooks.
-- The previous waybar, swaync, cliphist, hyprpaper, and hyprpolkitagent
-- entries are covered by the Quickshell bar; the CIFS share mounts from fstab.

local home = os.getenv("HOME")

hl.on("hyprland.start", function()
  -- Slow app launch fix: export the session environment to systemd/D-Bus.
  hl.exec_cmd("systemctl --user import-environment $(env | cut -d'=' -f 1)")
  hl.exec_cmd("dbus-update-activation-environment --systemd --all")

  -- Starts the Quickshell bar.
  hl.exec_cmd(home .. "/.local/bin/quickshell-desktop start")
  hl.exec_cmd("omarchy-powerprofiles-init")

  -- pywal16: recolor kitty from the wallpaper whenever the background changes.
  hl.exec_cmd(home .. "/.local/bin/wal-sync watch")

  -- VNC server for remote desktop via Cloudflare (desktop.thewaleed.me); localhost only.
  hl.exec_cmd(home .. "/.local/bin/wayvnc-keepalive")

  -- Accelerometer rotation; needs iio-sensor-proxy (monitor-sensor).
  if o.cmd_present("monitor-sensor") then
    hl.exec_cmd(home .. "/.config/hypr/screen-rotation.sh")
  end
end)
