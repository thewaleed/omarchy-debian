import QtQuick
import Quickshell
import Quickshell.Io
import "RotationModel.js" as RotationModel

Item {
  id: root

  // Injected by omarchy-shell (the first-party service loader).
  property var shell: null

  readonly property string home: Quickshell.env("HOME")
  readonly property var rotationConfig: shell && shell.shellConfig && shell.shellConfig.rotation
    ? shell.shellConfig.rotation : ({})
  readonly property int sensorOffset: Number(rotationConfig.sensorOffset) || 0
  readonly property string lockStatePath: home + "/.local/state/omarchy/indicators/rotation-lock"

  // Unknown until monitor-sensor answers; the indicator stays hidden on
  // machines without an accelerometer.
  property bool rotationAvailable: false
  property bool rotationLocked: false
  property bool lockStateLoaded: false
  property string orientation: ""
  property var appliedTransform: null
  property var pendingTransform: null
  property bool lockWritePending: false

  // The sensor is only claimed while auto-rotating, so a locked screen costs
  // nothing. Unlocking restarts monitor-sensor, whose first line reports the
  // current orientation, which snaps the screen to how the device is held.
  readonly property bool watching: lockStateLoaded && !rotationLocked

  onWatchingChanged: {
    sensorRestart.stop()
    sensorProcess.running = watching
  }

  function setRotationLocked(value) {
    var next = !!value
    if (lockStateLoaded && next === rotationLocked) return
    root.rotationLocked = next
    root.lockStateLoaded = true
    persistLock(next)
  }

  function toggle() {
    setRotationLocked(!rotationLocked)
  }

  function persistLock(value) {
    if (lockWriter.running) {
      root.lockWritePending = true
      return
    }
    lockWriter.command = ["bash", "-c", value
      ? "mkdir -p \"$(dirname \"$1\")\" && touch \"$1\""
      : "rm -f \"$1\"", "_", root.lockStatePath]
    lockWriter.running = true
  }

  function handleSensorLine(line) {
    var reading = RotationModel.parseSensorLine(line)
    if (!reading) return

    root.rotationAvailable = reading.available
    if (!reading.orientation) return

    root.orientation = reading.orientation
    var transform = RotationModel.transformForOrientation(reading.orientation, root.sensorOffset)
    if (transform !== null && !root.rotationLocked) applyTransform(transform)
  }

  function applyTransform(transform) {
    if (transform === root.appliedTransform && !rotateProcess.running) return
    if (rotateProcess.running) {
      root.pendingTransform = transform
      return
    }

    root.appliedTransform = transform
    // Keep the panel's current scale and position so rotating doesn't undo
    // whatever monitors.lua or the scaling/clamshell scripts settled on.
    // A disabled internal panel (clamshell) isn't listed, so it's left alone.
    rotateProcess.command = ["bash", "-c",
      "read -r name scale pos < <(hyprctl monitors -j | jq -r '[.[] | select(.name | test(\"^(eDP|LVDS|DSI)\"))][0] // empty | \"\\(.name) \\(.scale) \\(.x)x\\(.y)\"'); " +
      "[[ -n $name ]] || exit 0; " +
      "hyprctl eval \"hl.monitor({ output = \\\"$name\\\", mode = \\\"preferred\\\", position = \\\"$pos\\\", scale = $scale, transform = $1 })\" >/dev/null; " +
      "hyprctl eval \"hl.config({ input = { touchdevice = { transform = $1 } } })\" >/dev/null",
      "_", String(transform)]
    rotateProcess.running = true
  }

  Process {
    id: sensorProcess
    // monitor-sensor block-buffers stdout into a pipe; force line buffering
    // so orientation changes arrive as they happen. pdeathsig ends it with
    // the shell, which a restart kills without reaping its children.
    command: ["setpriv", "--pdeathsig", "TERM", "stdbuf", "-oL", "monitor-sensor", "--accel"]
    stdout: SplitParser {
      onRead: function(line) { root.handleSensorLine(line) }
    }
    onExited: function() {
      if (root.watching) sensorRestart.restart()
    }
  }

  Timer {
    id: sensorRestart
    interval: 5000
    onTriggered: if (root.watching && !sensorProcess.running) sensorProcess.running = true
  }

  Process {
    id: rotateProcess
    onExited: function() {
      if (root.pendingTransform === null) return
      var next = root.pendingTransform
      root.pendingTransform = null
      root.applyTransform(next)
    }
  }

  Process {
    id: lockWriter
    onExited: function() {
      if (!root.lockWritePending) return
      root.lockWritePending = false
      root.persistLock(root.rotationLocked)
    }
  }

  Process {
    id: lockProbe
    command: ["bash", "-c", "[[ -f $1 ]] && echo yes || echo no", "_", root.lockStatePath]
    stdout: SplitParser {
      onRead: function(line) {
        root.rotationLocked = String(line).trim() === "yes"
        root.lockStateLoaded = true
      }
    }
  }

  // Availability can't wait for monitor-sensor: a lock persisted from the
  // last session keeps the sensor unclaimed, and a hidden indicator could
  // never be unlocked. Asking iio-sensor-proxy directly doesn't claim it.
  Process {
    id: accelerometerProbe
    command: ["busctl", "get-property", "net.hadess.SensorProxy", "/net/hadess/SensorProxy",
      "net.hadess.SensorProxy", "HasAccelerometer"]
    stdout: SplitParser {
      onRead: function(line) { root.rotationAvailable = String(line).trim() === "b true" }
    }
  }

  Component.onCompleted: {
    accelerometerProbe.running = true
    lockProbe.running = true
  }

  IpcHandler {
    target: "rotation"

    function status(): string {
      return JSON.stringify({
        available: root.rotationAvailable,
        locked: root.rotationLocked,
        orientation: root.orientation,
        transform: root.appliedTransform
      })
    }

    function lock(): string {
      root.setRotationLocked(true)
      return "locked"
    }

    function unlock(): string {
      root.setRotationLocked(false)
      return "unlocked"
    }

    function toggle(): string {
      root.toggle()
      return root.rotationLocked ? "locked" : "unlocked"
    }
  }
}
