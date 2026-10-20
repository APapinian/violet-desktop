import QtQuick
import Quickshell
import Quickshell.Wayland
PanelWindow {
    id: popup
    property bool opened: false
    property Component body
    property int panelWidth: 400
    signal dismissed()
    anchors { top: true; right: true }
    margins { top: 74; right: 12 }
    implicitWidth: panelWidth
    implicitHeight: loader.implicitHeight + 40
    visible: frame.opacity > 0.001
    exclusionMode: ExclusionMode.Ignore
    color: 'transparent'
    focusable: opened
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: 'fatih-popup'
    Rectangle {
        id: frame
        anchors.fill: parent; radius: 28
        color: '#1d1927'; border.color: '#463c57'
        opacity: popup.opened ? 1 : 0
        scale: popup.opened ? 1 : .955
        transform: Translate {
            y: popup.opened ? 0 : -14
            Behavior on y { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
        }
        Behavior on opacity { NumberAnimation { duration: 210; easing.type: Easing.OutCubic } }
        Behavior on scale { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
        Loader {
            id: loader
            anchors.top: parent.top; anchors.left: parent.left; anchors.right: parent.right
            anchors.margins: 20
            sourceComponent: popup.body
        }
        focus: popup.opened
        Keys.onEscapePressed: popup.dismissed()
    }
}
