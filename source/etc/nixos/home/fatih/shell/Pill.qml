import QtQuick
Rectangle {
    id: pill
    property string label: ""
    property color fill: Theme.raised
    property color ink: Theme.pale
    property int horizontalPadding: 15
    signal clicked()
    implicitWidth: caption.implicitWidth + horizontalPadding * 2
    implicitHeight: 42
    radius: 11
    color: hit.containsMouse ? Qt.lighter(fill, 1.25) : fill
    border.color: hit.containsMouse ? Theme.accent : Theme.border
    border.width: 1
    scale: hit.pressed ? .96 : 1
    ClickRipple { id: ripple; anchors.fill: parent }
    Behavior on color { ColorAnimation { duration: Theme.duration(150) } }
    Behavior on scale { NumberAnimation { duration: Theme.duration(140) } }
    Text { id: caption; anchors.centerIn: parent; text: pill.label; color: pill.ink; font.family: Theme.sans; font.pixelSize: 12; textFormat: Text.PlainText }
    MouseArea { id: hit; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onPressed: mouse => ripple.burst(mouse.x, mouse.y); onClicked: pill.clicked() }
}
