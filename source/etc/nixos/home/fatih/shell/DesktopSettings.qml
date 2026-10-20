import QtQuick
import QtQuick.Layouts
ColumnLayout {
    id: settings
    required property var controller
    spacing: 18
    RowLayout {
        Layout.fillWidth:true
        ColumnLayout {
            Layout.fillWidth:true;spacing:5
            Text { text:"Masaüstü ayarları";color:Theme.pale;font.family:Theme.serif;font.pixelSize:26 }
            Text { text:"HYRULE  ·  QTILE";color:Theme.accent;font.family:Theme.sans;font.pixelSize:9;font.letterSpacing:2 }
        }
        Pill {label:"×";onClicked:settings.controller.openPanel=""}
    }
    RowLayout {Layout.fillWidth:true;Text {Layout.fillWidth:true;text:"ASCII Link eşlikçisi";color:Theme.pale} Pill {label:Theme.petEnabled ? "Açık" : "Kapalı";onClicked:Theme.petEnabled=!Theme.petEnabled}}
    RowLayout {Layout.fillWidth:true;Pill {label:"Kalem / kısayollar";onClicked:settings.controller.command(["violet-desktop","settings"])} Pill {label:"AI";onClicked:settings.controller.command(["violet-agent"])} Pill {label:"Telegram / SSH";onClicked:settings.controller.command(["violet-remote-settings"])}}
    Text {text:"HAREKET VE ATMOSFER";color:Theme.muted;font.family:Theme.sans;font.pixelSize:9;font.letterSpacing:2}
    RowLayout {
        Layout.fillWidth:true
        Repeater {
            model:[{id:"swift",name:"Çevik"},{id:"balanced",name:"Dengeli"},{id:"cinematic",name:"Sinematik"}]
            Pill {required property var modelData;Layout.fillWidth:true;label:modelData.name;fill:Theme.motionPreset===modelData.id ? "#46385d" : Theme.raised;onClicked:{Theme.reducedMotion=false;Theme.motionPreset=modelData.id;}}
        }
    }
    Control {Layout.fillWidth:true;label:"Geçiş temposu";value:(1.5-Theme.motionTempo)*100;onAdjusted:n=>Theme.motionTempo=1.5-n/100}
    RowLayout {Layout.fillWidth:true;Text {Layout.fillWidth:true;text:"Sade hareket";color:Theme.pale;font.family:Theme.sans;font.pixelSize:12} Pill {label:Theme.reducedMotion ? "Açık" : "Kapalı";onClicked:Theme.reducedMotion=!Theme.reducedMotion}}
    RowLayout {Layout.fillWidth:true;Text {Layout.fillWidth:true;text:"Ruh ışıkları";color:Theme.pale;font.family:Theme.sans;font.pixelSize:12} Pill {label:Theme.ambientEnabled ? "Açık" : "Kapalı";onClicked:Theme.ambientEnabled=!Theme.ambientEnabled}}
    RowLayout {Layout.fillWidth:true;Text {Layout.fillWidth:true;text:"Krallık karşılaması";color:Theme.pale;font.family:Theme.sans;font.pixelSize:12} Pill {label:Theme.welcomeEnabled ? "Açık" : "Kapalı";onClicked:Theme.welcomeEnabled=!Theme.welcomeEnabled}}
    Pill {Layout.fillWidth:true;label:"Karşılamayı yeniden oynat";onClicked:{settings.controller.openPanel="";settings.controller.showWelcome=false;Qt.callLater(()=>{settings.controller.showWelcome=true;settings.controller.restartWelcome();});}}
    Rectangle {Layout.fillWidth:true;implicitHeight:1;color:Theme.border}
    Text {text:"İŞARETÇİ VE DOKUNMATİK YÜZEY";color:Theme.muted;font.family:Theme.sans;font.pixelSize:9;font.letterSpacing:2}
    Control {Layout.fillWidth:true;label:"İşaretçi hızı";value:(Theme.pointerAccel+1)*50;onAdjusted:n=>Theme.pointerAccel=n/50-1}
    RowLayout {
        Layout.fillWidth:true
        Pill {Layout.fillWidth:true;label:"Uyarlanabilir";fill:Theme.pointerProfile==="adaptive" ? "#46385d" : Theme.raised;onClicked:Theme.pointerProfile="adaptive"}
        Pill {Layout.fillWidth:true;label:"Sabit ivme";fill:Theme.pointerProfile==="flat" ? "#46385d" : Theme.raised;onClicked:Theme.pointerProfile="flat"}
    }
    RowLayout {Layout.fillWidth:true;Text {Layout.fillWidth:true;text:"Doğal kaydırma";color:Theme.pale;font.family:Theme.sans;font.pixelSize:12} Pill {label:Theme.naturalScroll ? "Açık" : "Kapalı";onClicked:Theme.naturalScroll=!Theme.naturalScroll}}
    RowLayout {Layout.fillWidth:true;Text {Layout.fillWidth:true;text:"Dokunarak tıklama";color:Theme.pale;font.family:Theme.sans;font.pixelSize:12} Pill {label:Theme.tapToClick ? "Açık" : "Kapalı";onClicked:Theme.tapToClick=!Theme.tapToClick}}
    RowLayout {Layout.fillWidth:true;Text {Layout.fillWidth:true;text:"Yazarken yüzeyi durdur";color:Theme.pale;font.family:Theme.sans;font.pixelSize:12} Pill {label:Theme.disableWhileTyping ? "Açık" : "Kapalı";onClicked:Theme.disableWhileTyping=!Theme.disableWhileTyping}}
    RowLayout {Layout.fillWidth:true;Text {Layout.fillWidth:true;text:"Odak fareyi izlesin";color:Theme.pale;font.family:Theme.sans;font.pixelSize:12} Pill {label:Theme.focusFollowsMouse ? "Açık" : "Kapalı";onClicked:Theme.focusFollowsMouse=!Theme.focusFollowsMouse}}
    RowLayout {
        Layout.fillWidth:true
        Text {Layout.fillWidth:true;text:"İmleç boyutu";color:Theme.pale;font.family:Theme.sans;font.pixelSize:12}
        Repeater {model:[24,32,40];Pill {required property int modelData;label:String(modelData);fill:Theme.cursorSize===modelData ? "#46385d" : Theme.raised;onClicked:Theme.cursorSize=modelData}}
    }
    Pill {Layout.fillWidth:true;label:"İşaretçi tercihlerini uygula";onClicked:Theme.applyPointer()}
    Text {Layout.fillWidth:true;text:Theme.saveStatus || "Tercihler otomatik kaydedilir";color:Theme.muted;font.family:Theme.sans;font.pixelSize:10;wrapMode:Text.WordWrap}
    Rectangle {Layout.fillWidth:true;implicitHeight:1;color:Theme.border}
    Text {text:"PENCERE DÜZENİ";color:Theme.muted;font.family:Theme.sans;font.pixelSize:9;font.letterSpacing:2}
    RowLayout {
        Layout.fillWidth:true
        Pill {Layout.fillWidth:true;label:"Sonraki düzen";onClicked:settings.controller.command(["qtile","cmd-obj","-o","cmd","-f","next_layout"])}
        Pill {Layout.fillWidth:true;label:"Qtile'ı yenile";onClicked:settings.controller.command(["qtile","cmd-obj","-o","cmd","-f","reload_config"])}
    }
}
