-- Personal window rules, loaded after Omarchy's defaults.

-- xdg-desktop-portal-hyprland's screen-share picker otherwise tiles, which
-- hides it behind floating apps (e.g. Discord) and leaves the portal request
-- hanging. Float, center and pin it so it shows on whatever workspace is active.
o.window("hyprland-share-picker", { float = true, center = true, pin = true })
