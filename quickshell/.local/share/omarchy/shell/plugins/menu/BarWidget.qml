import QtQuick
import QtQuick.Effects
import qs.Ui

BarWidget {
  id: root
  moduleName: "omarchy.menu"

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  // Personal icon (assets/menu-icon.svg, traced from ~/thewaleed/test.png) in
  // place of the Omarchy logo glyph. It is drawn white and tinted with the
  // bar foreground, so it follows the theme like the other bar icons.
  readonly property real iconSize: Math.round(button.fontSize * 1.15)

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    hasVisualContent: true
    labelVisible: false
    horizontalMargin: 7.5
    fixedWidth: root.iconSize + scaledHorizontalMargin * 2
    onPressed: function(button) {
      if (!root.bar) return
      if (button === Qt.RightButton) root.bar.run("xdg-terminal-exec")
      else root.bar.run("omarchy-shell shell toggle omarchy.menu '{\"menu\":\"root\"}'")
    }

    Image {
      id: menuIcon
      anchors.centerIn: parent
      width: root.iconSize
      height: root.iconSize
      sourceSize: Qt.size(root.iconSize * 2, root.iconSize * 2)
      source: Qt.resolvedUrl("assets/menu-icon.svg")
      fillMode: Image.PreserveAspectFit
      smooth: true
      visible: false
    }

    MultiEffect {
      anchors.fill: menuIcon
      source: menuIcon
      colorization: 1.0
      colorizationColor: button.foreground
    }
  }
}
