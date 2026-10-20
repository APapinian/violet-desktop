import QtQuick
Item {
    id: welcome
    property bool opened: false
    property real reveal: 0
    property real orbit: 0
    property real titleReveal: 0
    signal dismissed()
    opacity: opened ? 1 : 0
    visible: opacity > .001
    Behavior on opacity { NumberAnimation { duration: Theme.duration(500); easing.type: Easing.InOutCubic } }
    onOpenedChanged: {
        if (opened) {
            if (Theme.reducedMotion) { reveal = 1; titleReveal = 1; }
            else { unveiling.restart(); lettering.restart(); }
        }
    }
    Rectangle { anchors.fill: parent; color: "#dd100f18" }
    SpiritMotes { anchors.fill: parent; active: welcome.opened; density: 26 }
    Item {
        width: 380; height: 380; anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: -90
        scale: .6 + welcome.reveal * .4; opacity: welcome.reveal
        Rectangle { anchors.centerIn: parent; width: 308; height: width; radius: width / 2; color: "transparent"; border.color: "#55463c57"; border.width: 1 }
        Rectangle { anchors.centerIn: parent; width: 258; height: width; radius: width / 2; color: "#15251a42"; border.color: "#998c77b3"; border.width: 1 }
        Item {
            anchors.fill: parent; rotation: welcome.orbit
            Repeater {
                model: 24
                Item {
                    required property int index
                    anchors.centerIn: parent; width: 308; height: 308; rotation: index * 15
                    Rectangle { anchors.horizontalCenter: parent.horizontalCenter; y: 0; width: index % 3 === 0 ? 7 : 2; height: index % 3 === 0 ? 7 : 11; rotation: index % 3 === 0 ? 45 : 0; color: Theme.accent; opacity: .35 + welcome.reveal * .5 }
                }
            }
        }
        Rectangle { anchors.centerIn: parent; width: 158; height: width; radius: width / 2; color: "#25251a42"; border.color: Theme.border }
        Sigil { anchors.centerIn: parent; width: 88; height: 88; scale: .85 + welcome.reveal * .15 }
        Rectangle { anchors.horizontalCenter: parent.horizontalCenter; y: 345; width: 160 * welcome.reveal; height: 1; color: Theme.accent; opacity: .7 }
    }
    Column {
        anchors.horizontalCenter: parent.horizontalCenter; anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: 152
        spacing: 18; opacity: welcome.titleReveal
        transform: Translate { y: 18 * (1 - welcome.titleReveal) }
        Text { text: "Krallığa hoş geldin, Fatih"; color: Theme.pale; font.family: Theme.serif; font.pixelSize: Math.min(42, welcome.width / 24); anchors.horizontalCenter: parent.horizontalCenter }
        Text { text: "H Y R U L E   ·   V I O L E T"; color: Theme.accent; font.family: Theme.sans; font.pixelSize: 10; font.letterSpacing: 3; anchors.horizontalCenter: parent.horizontalCenter }
        Text { text: "Yolculuk yeniden başlıyor"; color: Theme.muted; font.family: Theme.sans; font.pixelSize: 12; anchors.horizontalCenter: parent.horizontalCenter }
    }
    MouseArea { anchors.fill: parent; onClicked: welcome.dismissed() }
    focus: opened
    Keys.onEscapePressed: welcome.dismissed()
    NumberAnimation { id: unveiling; target: welcome; property: "reveal"; from: 0; to: 1; duration: Theme.duration(1800); easing.type: Easing.OutCubic }
    SequentialAnimation {
        id: lettering
        PropertyAction { target: welcome; property: "titleReveal"; value: 0 }
        PauseAnimation { duration: Theme.duration(650) }
        NumberAnimation { target: welcome; property: "titleReveal"; from: 0; to: 1; duration: Theme.duration(950); easing.type: Easing.OutCubic }
    }
    NumberAnimation on orbit { running: welcome.opened && !Theme.reducedMotion; from: 0; to: 120; duration: 12000; loops: Animation.Infinite }
}
