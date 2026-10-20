import QtQuick
import QtQuick.Layouts
ColumnLayout {
    id:panel
    required property var controller
    property var buds:controller.modern.state.bluetooth.buds || ({})
    spacing:18
    Text {text:panel.buds.name || "Galaxy Buds 3 Pro";color:Theme.pale;font.family:Theme.serif;font.pixelSize:28}
    Text {text:panel.buds.connected ? "● Bağlı" : "○ Bağlı değil";color:panel.buds.connected ? Theme.accent : Theme.muted;font.pixelSize:13}
    RowLayout {
        Layout.fillWidth:true;spacing:12
        Repeater {
            model:[{label:"Sol kulaklık",value:panel.buds.left},{label:"Sağ kulaklık",value:panel.buds.right},{label:"Şarj kutusu",value:panel.buds.case}]
            Rectangle {
                required property var modelData;Layout.fillWidth:true;implicitHeight:136;radius:18;color:Theme.raised
                Column {anchors.centerIn:parent;spacing:12
                    Text {anchors.horizontalCenter:parent.horizontalCenter;text:modelData.label;color:Theme.muted;font.pixelSize:11}
                    Text {anchors.horizontalCenter:parent.horizontalCenter;text:modelData.value===null || modelData.value===undefined ? "—" : modelData.value+"%";color:Theme.accent;font.pixelSize:32}
                    Text {anchors.horizontalCenter:parent.horizontalCenter;text:modelData.value===null || modelData.value===undefined ? "Veri alınmadı" : "Pil seviyesi";color:Theme.dim;font.pixelSize:10}
                }
            }
        }
    }
    Text {visible:panel.buds.battery!==null && panel.buds.battery!==undefined;text:"Bluetooth pil bildirimi: "+panel.buds.battery+"%";color:Theme.pale;font.pixelSize:13}
    Text {Layout.fillWidth:true;text:"Kaynak: "+(panel.buds.source || "Veri yok")+". Kutu kapalıysa şarj bilgisi gönderilmeyebilir.";wrapMode:Text.WordWrap;color:Theme.dim;font.pixelSize:11}
    Flow {
        Layout.fillWidth:true;spacing:8
        Pill {label:panel.buds.connected ? "Bağlantıyı kes" : "Bağlan";enabled:!!panel.buds.address;onClicked:panel.controller.modern.call(panel.buds.connected ? "buds-disconnect" : "buds-connect",{address:panel.buds.address})}
        Pill {label:"Eşleştir";onClicked:panel.controller.command(["blueman-manager"])}
        Pill {label:"Müzik / A2DP";enabled:panel.buds.connected;onClicked:panel.controller.modern.call("buds-profile",{address:panel.buds.address,mode:"music"})}
        Pill {label:"Görüşme / mikrofon";enabled:panel.buds.connected;onClicked:panel.controller.modern.call("buds-profile",{address:panel.buds.address,mode:"call"})}
        Pill {label:"Buds ayarları";onClicked:panel.controller.command(["GalaxyBudsClient"])}
        Pill {label:"Ses çıkışını seç";onClicked:{panel.controller.command(["violet-desktop","audio"]);}}
    }
    Text {Layout.fillWidth:true;text:panel.controller.modern.message;color:Theme.accent;font.pixelSize:12;wrapMode:Text.WordWrap;textFormat:Text.PlainText}
    Text {Layout.fillWidth:true;text:"İlk kullanımda Bluetooth menüsünden eşleştir, ardından Buds ayarlarında kulaklığı seç. Sol/sağ/kutu pili bu bağlantı kurulduğunda alınır.";color:Theme.muted;font.pixelSize:12;wrapMode:Text.WordWrap}
    Repeater {
        model:panel.controller.modern.state.bluetooth.items || []
        Text {required property var modelData;Layout.fillWidth:true;text:modelData.name+" · "+(modelData.connected ? "bağlı" : "kayıtlı")+(modelData.connected && modelData.battery!==null ? " · "+modelData.battery+"%" : "");color:Theme.muted;font.pixelSize:11;textFormat:Text.PlainText;elide:Text.ElideRight}
    }
}
