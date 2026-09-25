-- BEGIN hyprmoncfg wake settings
-- Shared with Omarchy while hyprmoncfg manages displays.
hl.monitor({ output = "eDP-1", mode = "preferred", position = "0x0", scale = 1.5 })
-- END hyprmoncfg wake settings
-- Startup monitor rule. The Display panel (omarchy-hyprland-monitor-scaling)
-- rewrites the scale and GDK_SCALE lines below in place, so keep their format.
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1.5 })

-- GTK only honors whole-number scales; see Omarchy's hypr/monitors.lua.
hl.env("GDK_SCALE", "2")
