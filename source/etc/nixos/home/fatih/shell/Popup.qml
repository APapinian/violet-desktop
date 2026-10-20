import QtQuick
import Quickshell
import Quickshell.Wayland
PanelWindow {
    id: popup
    property bool opened: false
    property Component body
    property int panelWidth: 408
    property bool centered:false
    signal dismissed()
    anchors { top: true; bottom: true; left: true; right: true }
    visible: scene.opacity > .001
    exclusionMode: ExclusionMode.Ignore
    color: "transparent"
    focusable: opened
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "fatih-hyrule-popup"
    Item {
        id: scene; anchors.fill: parent
        opacity: popup.opened ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: Theme.duration(180); easing.type: Easing.OutCubic } }
        Rectangle { anchors.fill: parent; color: "#22100f18" }
        MouseArea { objectName: "popupOutside"; anchors.fill: parent; enabled: popup.opened; onPressed: popup.dismissed() }
        RuneFrame {
            id: frame; objectName: "popupCard"
            anchors.right: popup.centered ? undefined : parent.right; anchors.rightMargin: 18
            anchors.horizontalCenter: popup.centered ? parent.horizontalCenter : undefined
            y: 54 + (popup.opened ? 0 : -24)
            width: Math.min(popup.panelWidth, scene.width - 36)
            height: Math.min(loader.implicitHeight + 56, scene.height - 96)
            radius: 32; ornament:false
            scale: popup.opened ? 1 : .96
            transformOrigin:Item.Top
            // Concave shoulders join the card to the same surface as the top ribbon.
            Rectangle { x:0;y:0;width:parent.width;height:32;color:Theme.surface }
            Canvas {
                x:-24;y:-1;width:parent.width+48;height:38
                onPaint:{let c=getContext("2d");c.clearRect(0,0,width,height);c.fillStyle=Theme.surface;c.beginPath();c.moveTo(0,0);c.lineTo(width,0);c.bezierCurveTo(width-22,0,width-24,12,width-24,36);c.lineTo(24,36);c.bezierCurveTo(24,12,22,0,0,0);c.fill();}
            }
            Behavior on y { NumberAnimation { duration: Theme.duration(330); easing.type: Easing.OutQuint } }
            Behavior on scale { NumberAnimation { duration: Theme.duration(330); easing.type: Easing.OutQuint } }
            MouseArea { anchors.fill: parent }
            Flickable {
                anchors.fill: parent; anchors.margins: 24; clip: true
                contentWidth: width; contentHeight: loader.implicitHeight
                boundsBehavior: Flickable.StopAtBounds
                Loader { id: loader; width: parent.width; active:popup.opened || scene.opacity>.001; sourceComponent: popup.body }
            }
            focus: popup.opened
            Keys.onEscapePressed: popup.dismissed()
        }
    }
}
