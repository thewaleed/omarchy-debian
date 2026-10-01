-- Personal bindings, merged from ~/thewaleed/dotfiles/.config/hypr/keybindings.conf
-- with a curated port of Omarchy's utilities/applications bindings.
-- Omarchy's tiling, media, and clipboard bindings load before this file;
-- o.rebind replaces an Omarchy default where the personal binding wins.
--
-- Deliberately omitted until their checkpoints land (see ~/dotfils/QUICKSHELL.md):
--   SUPER+L and XF86Lock locking, lid-switch lock,
--   keybinding viewer, agents/dictation, webapps, and apps that are not installed.

local paths = require("default.hypr.paths")

-- Omarchy helpers live on the launcher-private PATH, so check them by path.
local function present(command)
  local program = command:match("^%S+")
  if program:sub(1, 8) == "omarchy-" then
    return o.cmd_present(paths.omarchy_path .. "/bin/" .. program)
  end
  return o.cmd_present(program)
end

-- Bind only when the command exists, so a missing tool never leaves a dead key.
-- Always unbinds first, so a personal binding also clears Omarchy's default.
local function bind(keys, description, command, options)
  hl.unbind(keys)
  if type(command) ~= "string" or present(command) then
    o.bind(keys, description, command, options)
  end
end

local function toggle(keys, description, name, options)
  bind(keys, description, "omarchy-toggle-" .. name, options)
end

-- Window management (personal bindings win over Omarchy's).
bind("SUPER + F", "Toggle window floating/tiling", hl.dsp.window.float({ action = "toggle" }))
bind("SUPER + CTRL + F", "Full screen", hl.dsp.window.fullscreen({ mode = "fullscreen" }))
bind("SUPER + T", "Kill a window by clicking it", "hyprctl kill")
bind("SUPER + K", "Swap split", hl.dsp.layout("swapsplit"))
bind("SUPER + L", "Toggle workspace layout", "omarchy-hyprland-workspace-layout-toggle")
bind("SUPER + SHIFT + RIGHT", "Increase window width", hl.dsp.window.resize({ x = 100, y = 0, relative = true }))
bind("SUPER + SHIFT + LEFT", "Reduce window width", hl.dsp.window.resize({ x = -100, y = 0, relative = true }))
bind("SUPER + SHIFT + DOWN", "Increase window height", hl.dsp.window.resize({ x = 0, y = 100, relative = true }))
bind("SUPER + SHIFT + UP", "Reduce window height", hl.dsp.window.resize({ x = 0, y = -100, relative = true }))
bind("SUPER + TAB", "Next workspace on monitor", hl.dsp.focus({ workspace = "m+1" }))
bind("SUPER + SHIFT + TAB", "Previous workspace on monitor", hl.dsp.focus({ workspace = "m-1" }))

-- One scratchpad, named "magic" as before; Omarchy's scratchpad keys point to it too.
bind("SUPER + S", "Toggle scratchpad", hl.dsp.workspace.toggle_special("magic"))
bind("SUPER + grave", "Toggle scratchpad", hl.dsp.workspace.toggle_special("magic"))
bind("SUPER + SHIFT + S", "Move window to scratchpad", hl.dsp.window.move({ workspace = "special:magic" }))
bind("SUPER + ALT + S", "Move window silently to scratchpad", hl.dsp.window.move({ workspace = "special:magic", follow = false }))
bind("SUPER + SHIFT + grave", "Move window silently to scratchpad", hl.dsp.window.move({ workspace = "special:magic", follow = false }))

-- Workspaces stop at 9 (the bar shows up to 9), so drop Omarchy's SUPER+0 set.
hl.unbind("SUPER + code:19")
hl.unbind("SUPER + SHIFT + code:19")
hl.unbind("SUPER + SHIFT + ALT + code:19")

-- SUPER+L stays the workspace layout toggle; SUPER+CTRL+L locks.
bind("SUPER + CTRL + L", "Lock system", "omarchy-system-lock")

-- Applications.
bind("SUPER + RETURN", "Terminal", "omarchy-launch-terminal")
bind("SUPER + B", "Browser", "google-chrome-stable --ozone-platform=wayland")
bind("SUPER + SHIFT + RETURN", "Browser", "omarchy-launch-browser")
bind("SUPER + SHIFT + B", "Browser", "omarchy-launch-browser")
bind("SUPER + SHIFT + ALT + B", "Browser (private)", "omarchy-launch-browser --private")
bind("SUPER + E", "File manager", "nautilus --new-window")
bind("SUPER + SHIFT + F", "File manager", "nautilus --new-window")
bind("SUPER + CTRL + T", "Activity", "kitty --class org.omarchy.btop -e btop")

-- Menus.
bind("SUPER + SPACE", "Omarchy menu", "omarchy-menu toggle")
bind("SUPER + ALT + SPACE", "Apps menu", "omarchy-menu toggle apps")
bind("SUPER + R", "Apps menu", "omarchy-menu toggle apps")
bind("SUPER + CTRL + RETURN", "Apps menu", "omarchy-menu toggle apps")
bind("SUPER + period", "Emojis", "omarchy-shell shell toggle omarchy.emojis")
bind("SUPER + CTRL + E", "Emojis", "omarchy-shell shell toggle omarchy.emojis")
bind("SUPER + CTRL + C", "Capture menu", "omarchy-menu toggle capture")
bind("SUPER + CTRL + O", "Toggle menu", "omarchy-menu toggle toggle")
bind("SUPER + CTRL + H", "Hardware menu", "omarchy-menu toggle hardware")
bind("SUPER + ESCAPE", "System menu", "omarchy-menu toggle system")
bind("XF86PowerOff", "Power menu", "omarchy-menu toggle system", { locked = true })
bind("SUPER + CTRL + SPACE", "Background switcher", "omarchy-menu toggle background")
bind("SUPER + SHIFT + CTRL + SPACE", "Theme menu", "omarchy-menu toggle theme")

-- Clipboard: SUPER+V opens the clipboard manager (was cliphist + rofi).
-- Omarchy's universal copy/cut on SUPER+C/X stay.
bind("SUPER + V", "Clipboard manager", "omarchy-shell shell toggle omarchy.clipboard")
bind("SUPER + CTRL + V", "Clipboard manager", "omarchy-shell shell toggle omarchy.clipboard")

-- Bar and windows.
toggle("SUPER + SHIFT + SPACE", "Toggle top bar", "bar")
bind("SUPER + BACKSPACE", "Toggle window transparency", "omarchy-hyprland-window-transparency-toggle")
bind("SUPER + SHIFT + BACKSPACE", "Toggle window gaps", "omarchy-hyprland-window-gaps-toggle")
bind("SUPER + CTRL + BACKSPACE", "Toggle single-window square aspect", "omarchy-hyprland-window-single-square-aspect-toggle")
toggle("SUPER + CTRL + ALT + F", "Toggle full screen desktop", "fullscreen-desktop")

-- Notifications (SUPER+N replaces the swaync panel).
bind("SUPER + N", "Open notification history", "omarchy-shell notifications showHistory")
bind("SUPER + comma", "Dismiss last notification", "omarchy-shell notifications dismissOne")
bind("SUPER + SHIFT + comma", "Dismiss all notifications", "omarchy-shell notifications dismissAll")
toggle("SUPER + CTRL + comma", "Toggle silencing notifications", "notification-silencing")
toggle("SUPER + CTRL + I", "Toggle stay awake", "idle")
bind("SUPER + ALT + comma", "Invoke last notification", "omarchy-shell notifications invokeLast")
bind("SUPER + SHIFT + ALT + comma", "Open notification history", "omarchy-shell notifications showHistory")
bind("SUPER + CTRL + ALT + T", "Show time", "omarchy-notification-time")
bind("SUPER + CTRL + ALT + B", "Show battery remaining", "omarchy-notification-battery")

-- Capture (replaces hyprshot region/window/fullscreen).
bind("PRINT", "Screenshot", "omarchy-capture-screenshot")
bind("SHIFT + PRINT", "Screenshot window", "omarchy-capture-screenshot windows")
bind("CTRL + PRINT", "Screenshot full screen", "omarchy-capture-screenshot fullscreen")
-- Stops a running recording; otherwise opens the menu, which asks for audio,
-- then full screen / window / region.
bind("ALT + PRINT", "Screenrecording", "omarchy-capture-screenrecording --stop-recording || omarchy-menu toggle trigger.capture.screenrecord")
bind("SUPER + CTRL + PRINT", "Extract text (OCR) from screenshot", "omarchy-capture-text")

-- Keyboard control for the slurp region picker, ported from Omarchy's
-- utilities bindings (which this config does not load): Enter takes the
-- highlighted window, Ctrl+Enter the whole screen, Tab/arrows move between
-- windows. The binds exist only while a selection layer is on screen, and
-- each handle is removed individually so same-key personal binds survive.
local selection_layers = 0
local selection_binds = {}

hl.on("layer.opened", function(layer)
  if layer.namespace == "selection" then
    selection_layers = selection_layers + 1
    if selection_layers == 1 then
      selection_binds = {
        hl.bind("RETURN", hl.dsp.exec_cmd("omarchy-capture-region --take-window"), { description = "Capture highlighted window" }),
        hl.bind("CTRL + RETURN", hl.dsp.exec_cmd("omarchy-capture-region --take-fullscreen"), { description = "Capture entire screen" }),
        hl.bind("TAB", hl.dsp.exec_cmd("omarchy-capture-region --select-window next"), { description = "Select next window to capture" }),
        hl.bind("CTRL + TAB", hl.dsp.exec_cmd("omarchy-capture-region --select-window prev"), { description = "Select previous window to capture" }),
      }
      for _, direction in ipairs({ "left", "right", "up", "down" }) do
        table.insert(
          selection_binds,
          hl.bind(direction:upper(), hl.dsp.exec_cmd("omarchy-capture-region --select-window " .. direction), { description = "Select window to capture" })
        )
      end
    end
  end
end)

hl.on("layer.closed", function(layer)
  if layer.namespace == "selection" and selection_layers > 0 then
    selection_layers = selection_layers - 1
    if selection_layers == 0 then
      for _, keybind in ipairs(selection_binds) do
        keybind:unbind()
      end
      selection_binds = {}
    end
  end
end)
bind("SUPER + PRINT", "Color picker", "hyprpicker -a")

-- Panels.
bind("SUPER + CTRL + A", "Audio", "omarchy-shell shell toggle omarchy.audio")
bind("SUPER + CTRL + B", "Bluetooth", "omarchy-shell shell toggle omarchy.bluetooth")
bind("SUPER + CTRL + D", "Display", "omarchy-shell shell toggle omarchy.monitor")
bind("SUPER + CTRL + ALT + D", "Calendar", "omarchy-shell shell toggle omarchy.clock")
bind("SUPER + CTRL + W", "Network", "omarchy-shell shell toggle omarchy.network")
bind("SUPER + CTRL + P", "Power", "omarchy-shell shell toggle omarchy.power")
for panel = 1, 9 do
  bind("SUPER + CTRL + code:" .. tostring(panel + 9), "Bar panel " .. panel,
    "omarchy-shell -q shell togglePanelAt right " .. panel)
end

-- Zoom.
bind("SUPER + CTRL + Z", "Zoom in", function()
  local zoom = hl.get_config("cursor.zoom_factor") or 1
  hl.config({ cursor = { zoom_factor = zoom + 1 } })
end)
bind("SUPER + CTRL + ALT + Z", "Reset zoom", function()
  hl.config({ cursor = { zoom_factor = 1 } })
end)

bind("SUPER + M", "Exit Hyprland", hl.dsp.exit())
