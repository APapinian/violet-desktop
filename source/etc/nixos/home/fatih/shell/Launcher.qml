import QtQuick
import Quickshell
import Quickshell.Wayland
PanelWindow {
    id:overlay
    required property var controller
    property bool opened:false
    anchors { top:true; bottom:true; left:true; right:true }
    exclusionMode:ExclusionMode.Ignore; color:"transparent"
    visible:frame.opacity>.001; focusable:opened
    WlrLayershell.layer:WlrLayer.Overlay
    WlrLayershell.namespace:"fatih-hyrule-launcher"
    Rectangle {
        id:frame; anchors.fill:parent; color:"#99100f18"
        opacity:overlay.opened ? 1 : 0
        Behavior on opacity { NumberAnimation { duration:Theme.duration(180); easing.type:Easing.OutCubic } }
        MouseArea { anchors.fill:parent; onClicked:overlay.controller.openPanel="" }
        Item {
            anchors.centerIn:parent; width:Math.min(940,parent.width-60); height:Math.min(656,parent.height-110)
            scale:overlay.opened ? 1 : .96
            transform:Translate { y:overlay.opened ? 0 : 16; Behavior on y { NumberAnimation { duration:Theme.duration(280); easing.type:Easing.OutCubic } } }
            Behavior on scale { NumberAnimation { duration:Theme.duration(280); easing.type:Easing.OutCubic } }
            MouseArea { anchors.fill:parent }
            LauncherBody { anchors.fill:parent; controller:overlay.controller; opened:overlay.opened }
        }
    }
}
