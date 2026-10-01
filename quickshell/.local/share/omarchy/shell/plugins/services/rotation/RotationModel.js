// iio-sensor-proxy names the edge of the device that points up; Hyprland
// wants the wl_output transform that undoes that turn. Flat or unknown
// readings ("undefined") map to null so the screen keeps its last rotation.
//
// Some convertibles mount the accelerometer turned relative to the panel.
// sensorOffset (quarter turns, from shell.json "rotation.sensorOffset")
// corrects for that; e.g. 2 for a sensor that reads bottom-up when upright.
var TRANSFORMS = {
  "normal": 0,
  "left-up": 1,
  "bottom-up": 2,
  "right-up": 3
}

// monitor-sensor prints the starting orientation once it claims the sensor,
// then one line per change:
//   === Has accelerometer (orientation: bottom-up, tilt: tilted-down)
//       Accelerometer orientation changed: left-up
function parseSensorLine(line) {
  var text = String(line === undefined || line === null ? "" : line)
  if (text.indexOf("=== No accelerometer") !== -1) return { available: false, orientation: null }

  var initial = text.match(/=== Has accelerometer \(orientation: ([a-z-]+)/)
  if (initial) return { available: true, orientation: initial[1] }

  var changed = text.match(/Accelerometer orientation changed: ([a-z-]+)/)
  if (changed) return { available: true, orientation: changed[1] }

  return null
}

function transformForOrientation(orientation, sensorOffset) {
  if (!TRANSFORMS.hasOwnProperty(orientation)) return null
  var offset = Math.round(Number(sensorOffset) || 0)
  return (((TRANSFORMS[orientation] + offset) % 4) + 4) % 4
}

if (typeof module !== "undefined") {
  module.exports = {
    parseSensorLine: parseSensorLine,
    transformForOrientation: transformForOrientation
  }
}
