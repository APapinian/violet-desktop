import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import QtQuick.Controls as C

ColumnLayout {
    id:guide
    required property var controller
    property var rows:[]
    property int conflicts:0
    property string message:"Kısayollar okunuyor…"
    property string query:""
    spacing:16
    function matches(row) {return !query || (row.combo+" "+row.label+" "+row.category).toLocaleLowerCase().indexOf(query.toLocaleLowerCase())>=0;}
    Process {
        command:["cat",(Quickshell.env("XDG_RUNTIME_DIR") || "/run/user/1000")+"/fatih-shortcuts.json"]
        running:true
        stdout:SplitParser {onRead:line=>{
            try {const data=JSON.parse(line);guide.rows=data.rows || [];guide.conflicts=data.conflicts || 0;guide.message="Super = Windows tuşu. Tuş dizilerinde → işaretinden sonra tuşu ayrı bas.";}
            catch(e){guide.message="Kısayol listesi okunamadı. Qtile yapılandırmasını yeniden yükle.";}
        }}
        onExited:exitCode=>{if(exitCode!==0)guide.message="Kısayollar henüz etkin değil. Switch sonrası Qtile oturumunu yeniden aç.";}
    }
    RowLayout {
        Layout.fillWidth:true
        ColumnLayout {
            Layout.fillWidth:true;spacing:6
            Text {text:"Krallığın tuşları";color:Theme.pale;font.family:Theme.serif;font.pixelSize:29}
            Text {text:"KISAYOL REHBERİ";color:Theme.accent;font.family:Theme.sans;font.pixelSize:9;font.letterSpacing:2}
        }
        Pill {label:"×";onClicked:guide.controller.openPanel=""}
    }
    Text {Layout.fillWidth:true;text:guide.message;wrapMode:Text.WordWrap;color:Theme.muted;font.family:Theme.sans;font.pixelSize:12}
    C.TextField {
        Layout.fillWidth:true;placeholderText:"Ara: müzik, tablet, not, ekran…";color:Theme.pale;placeholderTextColor:Theme.dim
        font.family:Theme.sans;font.pixelSize:13;implicitHeight:44;leftPadding:14
        onTextChanged:guide.query=text
        background:Rectangle {color:Theme.background;radius:12;border.color:parent.activeFocus ? Theme.accent : Theme.border}
    }
    Text {Layout.fillWidth:true;visible:guide.conflicts>0;text:guide.conflicts+" yeni kısayol mevcut atamalarınla çakıştı; mevcut atamalar korundu.";wrapMode:Text.WordWrap;color:Theme.accent;font.pixelSize:12}
    ColumnLayout {
        Layout.fillWidth:true;spacing:5
        Repeater {
            model:guide.rows
            delegate:Rectangle {
                required property var modelData
                Layout.fillWidth:true;visible:guide.matches(modelData)
                implicitHeight:Math.max(keyLabel.implicitHeight,actionLabel.implicitHeight)+22
                radius:11;color:modelData.status==="conflict" ? Theme.background : Theme.surface
                border.color:modelData.status==="conflict" ? Theme.border : "transparent"
                RowLayout {
                    anchors.fill:parent;anchors.margins:11;spacing:14
                    Text {id:keyLabel;Layout.preferredWidth:190;Layout.maximumWidth:parent.width*.45;text:modelData.combo;color:Theme.accent;font.family:Theme.sans;font.pixelSize:12;wrapMode:Text.WrapAnywhere;textFormat:Text.PlainText}
                    Text {id:actionLabel;Layout.fillWidth:true;text:modelData.label+(modelData.status==="conflict" ? " · EKLENMEDİ" : "");color:Theme.pale;font.family:Theme.sans;font.pixelSize:12;wrapMode:Text.WrapAnywhere;textFormat:Text.PlainText}
                }
            }
        }
    }
}
