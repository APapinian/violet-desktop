import QtQuick
import Quickshell
import Quickshell.Wayland

PanelWindow {
    id: pet
    required property var controller
    anchors { bottom:true; left:true }
    margins.left: travel
    margins.bottom: 124
    implicitWidth: 258; implicitHeight: 166
    property real travel: 48
    property int step: 0
    property string face: "o o"
    property string remark: "Hey! Dinliyorum."
    property var jokes: ["Ganondorf bile bu kadar sekme açmaz.", "RAM öldü. Ruhuna bir swap.", "Kılıcı güncelledim. Bağımlılık: cesaret.", "Hyrule yandı. Yedek vardı, değil mi?", "sudo cesaret: yetki reddedildi.", "Bugün de sistemi kurtardık. Sistem bizden kurtulamadı."]
    visible: Theme.petEnabled && !controller.privateMode && !controller.fullscreen
    focusable:false; exclusionMode:ExclusionMode.Ignore; color:"transparent"
    WlrLayershell.layer: WlrLayer.Top
    WlrLayershell.namespace:"violet-ascii-spirit"
    Behavior on travel { NumberAnimation { duration: Theme.duration(5200); easing.type:Easing.InOutSine } }
    Timer { interval:6800;running:pet.visible && !Theme.reducedMotion;repeat:true;onTriggered:{pet.travel=Math.max(12,Math.random()*Math.max(24,(pet.screen ? pet.screen.width : 1280)-290));pet.step++;pet.face=["o o","- -","^ ^","O o"][pet.step%4];} }
    Timer { interval:22000;running:pet.visible;repeat:true;onTriggered:pet.remark=pet.jokes[Math.floor(Math.random()*pet.jokes.length)] }
    Connections {
        target:pet.controller
        function onStateChanged() { pet.face="o >";pet.remark="Pencere: "+String(pet.controller.state.application || "Masaüstü").substring(0,28); }
    }
    Column {
        anchors.fill:parent;spacing:7
        Rectangle {
            width:parent.width;height:42;radius:18;color:"#e8211b2d";border.color:Theme.border
            Text {anchors.fill:parent;anchors.margins:9;text:pet.remark;color:Theme.muted;wrapMode:Text.WordWrap;font.pixelSize:10;textFormat:Text.PlainText}
        }
        Text {
            anchors.horizontalCenter:parent.horizontalCenter
            text:"   /\\_\n  /___\\\n /("+pet.face+")\\\n   /|\\  /|\n  /_|_\\/_|\n   / \\"
            color:Theme.accent;font.family:"monospace";font.pixelSize:14;lineHeight:1.04;textFormat:Text.PlainText
            MouseArea { anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:{pet.face=pet.face==="^ ^" ? "O O" : "^ ^";pet.remark=pet.jokes[Math.floor(Math.random()*pet.jokes.length)];} }
        }
    }
}
