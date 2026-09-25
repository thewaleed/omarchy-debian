-- Stow-managed Hyprland 0.55 configuration for the Debian Quickshell port.
-- Loads Omarchy's defaults selectively from the imported runtime; the upstream
-- files under ~/.local/share/omarchy/default/hypr are never edited here.

local home = os.getenv("HOME")
local omarchy_path = os.getenv("OMARCHY_PATH")
if omarchy_path == nil or omarchy_path == "" then
  omarchy_path = home .. "/.local/share/omarchy"
end
-- Hyprland is started by the display manager, not by quickshell-desktop, so
-- publish the runtime root before any Omarchy module reads it.
hl.env("OMARCHY_PATH", omarchy_path)

-- bootstrap.lua and paths.lua read OMARCHY_PATH via os.getenv(), which hl.env
-- may not update inside this process. Pass the resolved root explicitly.
package.path = omarchy_path .. "/?.lua;" .. package.path
dofile(omarchy_path .. "/default/hypr/bootstrap.lua")
package.path = omarchy_path .. "/?.lua;" .. package.path
package.loaded["default.hypr.paths"] = {
  home = home,
  config_home = home .. "/.config",
  state_home = home .. "/.local/state",
  omarchy_path = omarchy_path,
}

require("default.hypr.helpers")
require("hypr.debian")
local require_optional = require("default.hypr.require_optional")

-- Omarchy defaults that work unchanged on Debian.
require("default.hypr.envs")
require("default.hypr.looknfeel")
-- default.hypr.qconsole needs the workspace.special_active event, which
-- Hyprland 0.55.2 does not provide; the agent console stays unloaded.
require("default.hypr.input")
require("default.hypr.windows")
require("default.hypr.bindings.tiling")
require("default.hypr.bindings.media")
require("default.hypr.bindings.clipboard")
-- Upstream utilities/applications/voxtype bindings are replaced by the curated
-- hypr.bindings module: they assume UWSM, lock/idle, and preinstalled apps.

require_optional.module("omarchy.current.theme.hyprland")

-- Personal overrides, loaded after the defaults.
require("hypr.monitors")
require("hypr.input")
require("hypr.bindings")
require("hypr.looknfeel")
require("hypr.windows")
require("hypr.autostart")

require("default.hypr.toggles")

-- Added by hyprmoncfg: its generated monitor rules load last, so nothing before this can override the applied layout.
do local path = os.getenv("HOME") .. "/.config/hypr/hyprmoncfg-monitors.lua"; local file = io.open(path, "r"); if file then file:close(); dofile(path) end end
