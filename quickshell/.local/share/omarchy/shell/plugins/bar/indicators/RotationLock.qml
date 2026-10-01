import QtQuick
import qs.Ui

BarIndicator {
  id: root

  readonly property var rotationService: bar?.shell?.firstPartyServiceFor("omarchy.rotation")
  readonly property bool available: !!rotationService && rotationService.rotationAvailable === true

  // Without an accelerometer there's nothing to lock, so take no slot at all.
  keepSpace: available
  active: available && rotationService.rotationLocked === true
  activeText: available ? "󰑹" : ""
  inactiveText: available ? "󰑸" : ""
  activeTooltipText: "Unlock Rotation"
  inactiveTooltipText: "Lock Rotation"

  onPressed: function() {
    if (root.rotationService) root.rotationService.setRotationLocked(!root.active)
  }
}
