import QtQuick
import QtQuick.Layouts
ColumnLayout {
    id: root
    property string label: ''
    property real value: 0
    property color accent: '#c5b4ff'
    signal adjusted(real number)
    spacing: 12
    RowLayout {
        Layout.fillWidth: true
        Text { Layout.fillWidth: true; text: root.label; color: '#ece4f8'; font.family: 'Rubik'; font.pixelSize: 14 }
        Text { text: Math.round(root.value) + '%'; color: root.accent; font.family: 'Rubik'; font.pixelSize: 14 }
    }
    Item {
        id: track
        Layout.fillWidth: true; implicitHeight: 32
        Rectangle { anchors.verticalCenter: parent.verticalCenter; width: parent.width; height: 8; radius: 4; color: '#373044' }
        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width * Math.max(0, Math.min(1, root.value/100)); height: 8; radius: 4; color: root.accent
            Behavior on width { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
        }
        Rectangle {
            x: Math.max(0, Math.min(track.width-width, track.width*root.value/100-width/2))
            anchors.verticalCenter: parent.verticalCenter
            width: hit.pressed ? 24 : 18; height: width; radius: width/2
            color: root.accent
            Behavior on width { NumberAnimation { duration: 160 } }
            Behavior on x { NumberAnimation { duration: 110; easing.type: Easing.OutCubic } }
        }
        MouseArea {
            id: hit; anchors.fill: parent; cursorShape: Qt.PointingHandCursor
            property real preview: 0
            function setPosition(x) { preview = Math.round(100*Math.max(0,Math.min(1,x/width))); root.adjusted(preview); }
            // Audio writes are native and cheap; brightness command is committed on release by the parent.
            onPressed: setPosition(mouse.x)
            onPositionChanged: if (pressed) setPosition(mouse.x)
        }
    }
}
