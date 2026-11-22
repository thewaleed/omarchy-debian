-- GNOME Network Displays (Miracast / Chromecast casting) is a small picker; float it.
o.window({ class = "^org.gnome.NetworkDisplays$" }, {
  float = true,
  center = true,
  size = { 600, 500 },
})
