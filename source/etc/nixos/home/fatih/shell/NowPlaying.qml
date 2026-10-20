import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland

PanelWindow {
    id: overlay
    required property var controller
    property var track: controller.features.data("media").current || ({})
    property bool opened: controller.nowPlayingOpen && !controller.privateMode
    anchors { top: true; right: true }
    margins { top: 76; right: 18 }
    implicitWidth: 470
    implicitHeight: 206
    visible: card.opacity > .001
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore
    focusable: false
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "fatih-violet-now-playing"

    RuneFrame {
        id: card
        anchors.fill: parent
        anchors.margins: 5
        radius: 22
        opacity: overlay.opened ? 1 : 0
        transform: Translate { y: overlay.opened ? 0 : -12; Behavior on y { NumberAnimation { duration: Theme.duration(220) } } }
        Behavior on opacity { NumberAnimation { duration: Theme.duration(180) } }
        RowLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 16
            Rectangle {
                Layout.preferredWidth: 102; Layout.preferredHeight: 102
                color: Theme.raised; radius: 14; clip: true
                Image { anchors.fill: parent; source: overlay.track.art || ""; fillMode: Image.PreserveAspectCrop; asynchronous: true }
                Sigil { anchors.centerIn: parent; width: 38; height: 38; name: "music"; visible: !overlay.track.art }
            }
            ColumnLayout {
                Layout.fillWidth: true; spacing: 8
                Text { text: "ŞİMDİ ÇALIYOR"; color: Theme.accent; font.pixelSize: 9; font.letterSpacing: 2 }
                Text { Layout.fillWidth: true; text: overlay.track.title || "Henüz bir şey çalmıyor"; color: Theme.pale; font.family: Theme.serif; font.pixelSize: 20; elide: Text.ElideRight; textFormat: Text.PlainText }
                Text { Layout.fillWidth: true; text: overlay.track.artist || "Oynatıcından bir parça başlat"; color: Theme.muted; font.pixelSize: 11; elide: Text.ElideRight; textFormat: Text.PlainText }
                RowLayout {
                    spacing: 6
                    Repeater {
                        model: [{label:"◀",command:"previous"},{label:overlay.track.status==="Playing" ? "Ⅱ" : "▶",command:"play-pause"},{label:"▶▶",command:"next"}]
                        Pill {
                            required property var modelData
                            label: modelData.label; horizontalPadding: 12; implicitHeight: 32
                            enabled: !!overlay.track.player
                            onClicked: overlay.controller.modern.call("player", {player:overlay.track.player, command:modelData.command})
                        }
                    }
                    Pill { label: "Aç"; implicitHeight: 32; horizontalPadding: 10; onClicked: {overlay.controller.nowPlayingOpen=false;overlay.controller.modernTab="media";overlay.controller.openPanel="modern";} }
                }
            }
            Text {
                Layout.alignment: Qt.AlignTop; text: "×"; color: Theme.muted; font.pixelSize: 22
                MouseArea { anchors.fill: parent; anchors.margins: -6; onClicked: overlay.controller.nowPlayingOpen=false }
            }
        }
    }
}
