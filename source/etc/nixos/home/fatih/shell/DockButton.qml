import QtQuick
Item {
    id: button
    property string icon: "rune"
    property string iconSource: ""
    property string label: ""
    property bool active: false
    property bool running: false
    signal clicked()
    signal hovered(string caption)
    implicitWidth: 62; implicitHeight: 66
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter; y: hit.containsMouse ? 1 : 7
        width: 48; height: 48; radius: 15
        rotation: hit.containsMouse && !Theme.reducedMotion ? (hit.pressed ? 0 : -3) : 0
        Behavior on rotation { NumberAnimation {duration:Theme.duration(220);easing.type:Easing.OutCubic} }
        color: button.active ? "#46385d" : hit.containsMouse ? "#332b45" : "#251f32"
        border.color: button.active || hit.containsMouse ? Theme.accent : "#3b324c"
        scale: hit.pressed ? .93 : hit.containsMouse ? 1.06 : 1
        Behavior on y { NumberAnimation { duration: Theme.duration(180); easing.type: Easing.OutCubic } }
        Behavior on scale { NumberAnimation { duration: Theme.duration(180); easing.type: Easing.OutCubic } }
        ClickRipple { id:ripple;anchors.fill:parent }
        Behavior on color { ColorAnimation { duration: Theme.duration(150) } }
        Sigil { anchors.centerIn: parent; width: 27; height: 27; name: button.icon; visible: !button.iconSource }
        Image { anchors.centerIn: parent; width: 29; height: 29; source: button.iconSource; sourceSize: Qt.size(58,58); fillMode: Image.PreserveAspectFit; visible: !!button.iconSource }
    }
    Rectangle { anchors.horizontalCenter: parent.horizontalCenter; y: 61; width: button.active ? 13 : 4; height: 3; radius: 2; color: Theme.accent; visible: button.running || button.active; Behavior on color { ColorAnimation {duration:Theme.duration(160)} } Behavior on width { NumberAnimation { duration: Theme.duration(160) } } }
    MouseArea {
        id: hit; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
        onPressed: mouse=>ripple.burst(mouse.x-7,mouse.y-7)
        onClicked: button.clicked()
        onContainsMouseChanged: button.hovered(containsMouse ? button.label : "")
    }
}
