import QtQuick
import QtQuick.Layouts
RuneFrame {
    id: capsule
    required property var controller
    property var bridge: controller.features
    property int headlineIndex:0
    property bool music:!!bridge.data("media").current
    property var headlines:bridge.state.headlines || []
    property var headline:headlines.length ? headlines[headlineIndex % headlines.length] : null
    property var current:bridge.data("media").current || ({})
    RowLayout {
        anchors.fill:parent;anchors.margins:10;spacing:8
        Sigil {name:capsule.music ? "music" : "rune";Layout.preferredWidth:20;Layout.preferredHeight:20}
        Text {
            Layout.fillWidth:true;elide:Text.ElideRight;font.pixelSize:11;color:Theme.pale;textFormat:Text.PlainText
            text:capsule.music ? (capsule.current.title || "Müzik") : capsule.headline ? (capsule.headline.title || "Haber") : "Krallığın akışı  ›"
            opacity:headlineChange.running ? .55 : 1
            Behavior on opacity {NumberAnimation {duration:Theme.duration(180)}}
        }
        Text {text:capsule.bridge.state.pomodoro.running ? Math.floor(capsule.bridge.state.pomodoro.remaining/60)+":"+String(capsule.bridge.state.pomodoro.remaining%60).padStart(2,"0") : "◇";font.pixelSize:10;color:Theme.accent}
    }
    Timer {id:headlineChange;interval:9000;repeat:true;running:!capsule.music && capsule.headlines.length>1;onTriggered:capsule.headlineIndex++}
    MouseArea {anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:{capsule.controller.featureSection=capsule.music ? "media" : "daily";capsule.controller.toggle("features");}}
}
