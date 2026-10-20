import QtQuick
Rectangle {
    id: frame
    property bool ornament: true
    color: Theme.surface
    radius: 20
    border.color: Theme.border
    border.width: 1
    Rectangle { anchors.fill: parent; anchors.margins: 4; radius: parent.radius-4; color: "transparent"; border.color: "#202b2238" }
    Item {
        visible: frame.ornament
        width: 34; height: 6
        anchors.horizontalCenter: parent.horizontalCenter; y: -3
        Rectangle { width: 6; height: 6; rotation: 45; color: Theme.accent; anchors.centerIn: parent }
        Rectangle { width: 9; height: 1; color: Theme.border; anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter }
        Rectangle { width: 9; height: 1; color: Theme.border; anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter }
    }
}
