import QtQuick
import QtQuick.Layouts
RowLayout {
    id:player
    required property var controller
    property var results:[]
    property var selectedTrack: (controller.features.data("media").players || []).find(p=>p.player===controller.mediaPlayer) || controller.features.data("media").current || ({})
    property var queue: selectedTrack.player && selectedTrack.player.indexOf("mpv")>=0 ? controller.features.state.upcoming || [] : []
    spacing:22
    RecordDeck {Layout.fillWidth:true;Layout.preferredWidth:470;controller:player.controller}
    Rectangle {
        Layout.preferredWidth:Math.min(310,player.width*.38);Layout.fillHeight:true;Layout.minimumHeight:530;radius:18;color:Theme.raised
        ColumnLayout {
            anchors.fill:parent;anchors.margins:18;spacing:12
            Text {text:"Çalma sırası";color:Theme.pale;font.pixelSize:18}
            Text {text:"Yerel çalma sırası · mpv";color:Theme.dim;font.pixelSize:10}
            Repeater {
                model:player.queue
                Rectangle {
                    required property var modelData;Layout.fillWidth:true;implicitHeight:56;radius:10;color:Theme.surface
                    Text {anchors.fill:parent;anchors.margins:12;text:modelData.title || "Parça";color:Theme.pale;font.pixelSize:12;elide:Text.ElideRight;textFormat:Text.PlainText}
                }
            }
            Text {Layout.fillWidth:true;visible:!player.queue.length;text:"Bu oynatıcı sıra paylaşmıyor.";wrapMode:Text.WordWrap;color:Theme.dim;font.pixelSize:11}
            Rectangle {Layout.fillWidth:true;implicitHeight:1;color:Theme.border}
            KingdomInput {id:search;Layout.fillWidth:true;placeholderText:"YouTube Music'te ara";onAccepted:player.controller.features.call("search-music",text)}
            Pill {label:"Ara";onClicked:player.controller.features.call("search-music",search.text)}
            Repeater {
                model:player.results.slice(0,5)
                ColumnLayout {
                    required property var modelData
                    Layout.fillWidth:true
                    Text {Layout.fillWidth:true;text:modelData.title;color:Theme.pale;font.pixelSize:12;elide:Text.ElideRight;textFormat:Text.PlainText}
                    RowLayout {Pill {label:"Oynat";onClicked:player.controller.features.call("play",modelData)} Pill {label:"+ Sıra";onClicked:player.controller.features.call("enqueue",modelData)}}
                }
            }
            Item {Layout.fillHeight:true}
            Text {Layout.fillWidth:true;text:player.controller.features.message;color:Theme.dim;font.pixelSize:11;wrapMode:Text.WordWrap;textFormat:Text.PlainText}
        }
    }
    Connections {target:player.controller.features;function onCompleted(action,result){if(action==="search-music")player.results=result;}}
}
