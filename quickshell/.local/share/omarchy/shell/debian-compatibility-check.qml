import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Shapes
import QtQuick.Effects
import QtQml.Models
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import Quickshell.Wayland
import Quickshell.Networking
import Quickshell.Bluetooth
import Quickshell.Services.Notifications
import Quickshell.Services.Pipewire
import Quickshell.Services.Mpris
import Quickshell.Services.UPower
import Quickshell.Services.SystemTray
import Quickshell.Services.Pam
import Quickshell.Services.Polkit

// Non-visual compilation probe. No plugin is instantiated: no panels, service
// ownership, lock requests, network actions, or compositor dispatches.
ShellRoot {
  Timer {
    interval: 10
    running: true
    onTriggered: {
      var paths = JSON.parse(Quickshell.env("OMARCHY_CHECK_COMPONENTS") || "[]")
      var failed = 0
      for (var i = 0; i < paths.length; i++) {
        var component = Qt.createComponent(Qt.resolvedUrl(paths[i]), Component.PreferSynchronous)
        if (component.status !== Component.Ready) {
          console.error("COMPONENT_FAILED", paths[i], component.errorString())
          failed++
        }
      }
      if (failed === 0) console.log("DEBIAN_COMPONENT_CHECK_OK", paths.length)
      Qt.exit(failed === 0 ? 0 : 1)
    }
  }
}
