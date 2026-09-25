-- Debian overrides for Omarchy's Hyprland helpers.
-- UWSM is not installed; Hyprland's exec already detaches launched commands.

function o.launch(command)
  return command
end
