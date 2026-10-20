import QtQuick
import QtQuick.Layouts
ColumnLayout {
    id: card
    required property var bridge
    property var current:bridge.data("media").current || ({})
    spacing: 14
    RowLayout {
        Layout.fillWidth:true;spacing:18
        Rectangle {
            Layout.preferredWidth:132;Layout.preferredHeight:132;radius:18;clip:true;color:Theme.ink
            Image {anchors.fill:parent;source:card.current.art || "";sourceSize:Qt.size(264,264);fillMode:Image.PreserveAspectCrop;asynchronous:true;cache:true}
            Sigil {anchors.centerIn:parent;width:40;height:40;name:"music";visible:!card.current.art}
        }
        ColumnLayout {
            Layout.fillWidth:true
            Text {Layout.fillWidth:true;text:card.current.title || "Henüz bir şey çalmıyor";color:Theme.pale;font.family:Theme.serif;font.pixelSize:23;wrapMode:Text.WordWrap;textFormat:Text.PlainText}
            Text {Layout.fillWidth:true;text:card.current.artist || "MPRIS yayımlayan oynatıcıları dinler";color:Theme.muted;font.pixelSize:12;wrapMode:Text.WordWrap;textFormat:Text.PlainText}
            Text {Layout.fillWidth:true;text:card.current.album || "";color:Theme.dim;font.pixelSize:11;textFormat:Text.PlainText;elide:Text.ElideRight}
            RowLayout {
                Repeater {
                    model:[{id:"previous",label:"‹"},{id:"play-pause",label:card.current.status==="Playing" ? "Duraklat" : "Oynat"},{id:"next",label:"›"}]
                    Pill {required property var modelData;label:modelData.label;onClicked:if(card.current.player) card.bridge.call("player",{player:card.current.player,command:modelData.id})}
                }
            }
        }
    }
    Text {Layout.fillWidth:true;text:card.bridge.state.lyrics.line || card.bridge.state.lyrics.status || "";color:Theme.accent;font.family:Theme.serif;font.pixelSize:17;wrapMode:Text.WordWrap;textFormat:Text.PlainText}
    Flow {
        Layout.fillWidth:true;spacing:8
        Repeater {model:card.bridge.data("media").players || [];Pill {required property var modelData;label:modelData.player;onClicked:card.bridge.call("player",{player:modelData.player,command:"play-pause"})}}
    }
}
