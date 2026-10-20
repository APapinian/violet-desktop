import QtQuick
Rectangle {
    id: pill
    property string label: ''
    property color fill: '#262331'
    property color ink: '#e9e1f5'
    property int horizontalPadding: 16
    signal clicked()
    implicitWidth: textItem.implicitWidth + horizontalPadding * 2
    implicitHeight: 36
    radius: height / 2
    color: hit.containsMouse ? Qt.lighter(fill, 1.16) : fill
    scale: hit.pressed ? 0.94 : hit.containsMouse ? 1.025 : 1
    Behavior on color { ColorAnimation { duration: 180 } }
    Behavior on scale { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
    Text {
        id: textItem; anchors.centerIn: parent
        text: pill.label; color: pill.ink
        font.family: 'Rubik'; font.pixelSize: 13; font.weight: Font.Medium
        Behavior on color { ColorAnimation { duration: 180 } }
    }
    MouseArea {
        id: hit; anchors.fill: parent; hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: pill.clicked()
    }
}
