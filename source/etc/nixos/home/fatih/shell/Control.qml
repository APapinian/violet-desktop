import QtQuick
import QtQuick.Layouts
ColumnLayout {
    id: control
    property string label: ""
    property real value: 0
    property string suffix: "%"
    property color accent: Theme.accent
    signal adjusted(real number)
    spacing: 10
    RowLayout {
        Layout.fillWidth: true
        Text { Layout.fillWidth: true; text: control.label; color: Theme.pale; font.family: Theme.sans; font.pixelSize: 13 }
        Text { text: Math.round(control.value) + control.suffix; color: control.accent; font.family: Theme.sans; font.pixelSize: 13 }
    }
    Item {
        id: track; Layout.fillWidth: true; implicitHeight: 40
        Rectangle { anchors.verticalCenter: parent.verticalCenter; width: parent.width; height: 5; radius: 3; color: Theme.border }
        Rectangle { anchors.verticalCenter: parent.verticalCenter; width: parent.width * Math.max(0,Math.min(1,control.value/100)); height: 5; radius: 3; color: control.accent; Behavior on width { NumberAnimation { duration: Theme.duration(120); easing.type:Easing.OutCubic } } }
        Rectangle {
            x: Math.max(0,Math.min(track.width-width,track.width*control.value/100-width/2)); anchors.verticalCenter: parent.verticalCenter
            width: 14; height: 14; rotation: 45; radius: 3; color: control.accent
            scale: hit.pressed ? 1.25 : hit.containsMouse ? 1.12 : 1
            Behavior on scale { NumberAnimation { duration:Theme.duration(130) } }
        }
        MouseArea {
            id:hit;hoverEnabled:true
            anchors.fill: parent; cursorShape: Qt.PointingHandCursor
            function adjust(x) { control.adjusted(Math.round(100*Math.max(0,Math.min(1,x/width)))); }
            onWheel: wheel => {control.adjusted(Math.max(0,Math.min(100,control.value+(wheel.angleDelta.y>0 ? 2 : -2))));wheel.accepted=true;}
            onPressed: mouse => adjust(mouse.x)
            onPositionChanged: mouse => { if (pressed) adjust(mouse.x); }
        }
    }
}
