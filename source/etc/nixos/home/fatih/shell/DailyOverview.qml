import QtQuick
import QtQuick.Layouts
ColumnLayout {
    id: daily
    required property var controller
    property var metrics: controller.modern.state
    property var track: controller.features.data("media").current || ({})
    spacing: 14
    RowLayout {
        Layout.fillWidth: true; spacing: 14
        Rectangle {
            Layout.fillWidth: true; implicitHeight: 114; radius: 19; color: Theme.raised
            Column {
                anchors.fill: parent; anchors.margins: 19; spacing: 9
                Text { text: daily.controller.features.state.location || "Hava durumu"; color: Theme.accent; font.pixelSize: 12 }
                Text { text: daily.controller.features.data("weather").current ? daily.controller.features.data("weather").current.temperature_2m+"°" : "—°"; color: Theme.pale; font.pixelSize: 34 }
                Text { width: parent.width; text: daily.controller.state.wifi || "Bağlantı bekleniyor"; color: Theme.muted; font.pixelSize: 10; elide: Text.ElideRight; textFormat: Text.PlainText }
            }
            MouseArea { anchors.fill: parent; onClicked: daily.controller.modernTab="weather" }
        }
        Rectangle {
            Layout.fillWidth: true; implicitHeight: 114; radius: 19; color: Theme.raised
            RowLayout {
                anchors.fill: parent; anchors.margins: 20; spacing: 15
                Sigil { width: 34; height: 34 }
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 8
                    Text { text: "Hoş geldin, Fatih"; color: Theme.pale; font.family: Theme.serif; font.pixelSize: 21 }
                    Text { text: "NixOS · Qtile Wayland"; color: Theme.muted; font.pixelSize: 11 }
                    Text { text: Math.floor(daily.metrics.uptime/3600)+" saat açık"; color: Theme.accent; font.pixelSize: 10 }
                }
            }
        }
    }
    RowLayout {
        Layout.fillWidth: true; spacing: 14
        Rectangle {
            Layout.fillWidth: true; Layout.preferredWidth: 405; implicitHeight: 362; radius: 19; color: Theme.raised
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 18; spacing: 10
                Text {text:daily.controller.timeText;color:Theme.accent;font.pixelSize:38}
                MiniCalendar {Layout.fillWidth:true}
                Item {Layout.fillHeight:true}
            }
        }
        Rectangle {
            Layout.preferredWidth: 106; implicitHeight: 362; radius: 19; color: Theme.raised
            Column { anchors.centerIn: parent; spacing: 19
                MetricRing { width: 80; height: 90; value: daily.metrics.cpu; label: "CPU" }
                MetricRing { width: 80; height: 90; value: daily.metrics.memory; label: "Bellek" }
                MetricRing { width: 80; height: 90; value: daily.metrics.disk; label: "Disk" }
            }
        }
        Rectangle {
            Layout.fillWidth: true; Layout.preferredWidth: 280; implicitHeight: 362; radius: 19; color: Theme.raised
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 18; spacing: 12
                Rectangle {
                    Layout.alignment: Qt.AlignHCenter; Layout.preferredWidth: 158; Layout.preferredHeight: 158
                    radius: 79; color: Theme.surface; clip: true; border.color: Theme.border
                    Canvas {
                        anchors.fill: parent
                        property string art: daily.track.art || ""
                        onArtChanged: {if(art)loadImage(art);requestPaint();}
                        Component.onCompleted: if(art)loadImage(art)
                        onImageLoaded: requestPaint()
                        onPaint: {const c=getContext("2d");c.reset();c.save();c.beginPath();c.arc(width/2,height/2,width/2-6,0,Math.PI*2);c.clip();if(art && isImageLoaded(art))c.drawImage(art,0,0,width,height);c.restore();}
                    }
                    Sigil { anchors.centerIn: parent; width: 40; height: 40; name: "music"; visible: !daily.track.art }
                }
                Text { Layout.fillWidth: true; text: daily.track.title || "Melodilerini aç"; color: Theme.pale; font.family: Theme.serif; font.pixelSize: 19; elide: Text.ElideRight; horizontalAlignment: Text.AlignHCenter; textFormat: Text.PlainText }
                Text { Layout.fillWidth: true; text: daily.track.artist || "Müzik, burada seninle"; color: Theme.muted; font.pixelSize: 11; elide: Text.ElideRight; horizontalAlignment: Text.AlignHCenter; textFormat: Text.PlainText }
                RowLayout {
                    Layout.alignment: Qt.AlignHCenter; spacing: 6
                    Repeater {
                        model: [{label:"◀",command:"previous"},{label:daily.track.status==="Playing" ? "Ⅱ" : "▶",command:"play-pause"},{label:"▶▶",command:"next"}]
                        Pill { required property var modelData; label: modelData.label; horizontalPadding: 13; implicitHeight: 37; enabled: !!daily.track.player; onClicked: daily.controller.modern.call("player",{player:daily.track.player,command:modelData.command}) }
                    }
                }
                Item { Layout.fillHeight: true }
                Pill { Layout.alignment: Qt.AlignHCenter; label: "Medya paneli  ›"; implicitHeight: 34; onClicked: daily.controller.modernTab="media" }
            }
        }
    }
    Flow {
        Layout.fillWidth: true; spacing: 7
        Repeater {
            model: [{label:"MyBrain",args:["mybrain-python"]},{label:"Dosyalar",args:["nautilus"]},{label:"Komut paleti",args:["violet-desktop","palette"]},{label:"Pencereler",args:["violet-desktop","overview"]},{label:"Masaüstü ayarları",args:["violet-desktop","settings"]}]
            Pill { required property var modelData; label: modelData.label; implicitHeight: 34; onClicked: daily.controller.command(modelData.args) }
        }
    }
}
