import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io

ColumnLayout {
    id: notices
    required property var controller
    property var rows: []
    property string error: ""
    function collect(value, result) {
        if (Array.isArray(value)) { for (let item of value) collect(item,result); }
        else if (value && typeof value==="object") {
            if (value.summary!==undefined) result.push(value);
            else for (let key of Object.keys(value)) collect(value[key],result);
        }
    }
    spacing:14
    RowLayout {
        Layout.fillWidth:true
        Text {text:"Bildirimler";color:Theme.pale;font.family:Theme.serif;font.pixelSize:26}
        Item {Layout.fillWidth:true}
        Pill {label:"Geçmiş";onClicked:controller.command(["violet-desktop","notifications"])}
        Pill {label:"×";onClicked:controller.openPanel=""}
    }
    Text {visible:notices.error!=="";text:notices.error;color:Theme.muted;textFormat:Text.PlainText}
    Text {visible:notices.rows.length;text:"Şimdilik sessiz. Krallık nefes alıyor.";color:Theme.muted}
    Repeater {
        model:notices.rows.slice(0,12)
        Rectangle {
            required property var modelData
            Layout.fillWidth:true;implicitHeight:label.implicitHeight+30;radius:22;color:Theme.raised
            Text {id:label;anchors.fill:parent;anchors.margins:15;text:(modelData.app_name || "Uygulama")+"\n"+(modelData.summary || "")+"\n"+String(modelData.body || "").replace(/<[^>]*>/g,"");textFormat:Text.PlainText;color:Theme.pale;font.pixelSize:12;wrapMode:Text.WordWrap}
        }
    }
    Process {
        id: refresh;command:["makoctl","list","-j"];running:true
        stdout:StdioCollector {onStreamFinished:{try {let result=[];notices.collect(JSON.parse(text),result);notices.rows=result;notices.error="";}catch(e){notices.error="Bildirimler okunamadı";}}}
    }
    Timer {interval:3000;repeat:true;running:true;onTriggered:if(!refresh.running)refresh.running=true}
}
