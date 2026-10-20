import QtQuick
import Quickshell
import Quickshell.Wayland
PanelWindow {
    id:ring
    required property var controller
    objectName:"violetPenMenu"
    anchors {top:true;bottom:true;left:true;right:true}
    screen:Quickshell.screens.find(s=>controller.penX>=s.x && controller.penX<s.x+s.width && controller.penY>=s.y && controller.penY<s.y+s.height) || Quickshell.screens[0]
    visible:controller.penOpened && !controller.privateMode
    focusable:visible;exclusionMode:ExclusionMode.Ignore;color:"transparent"
    WlrLayershell.layer:WlrLayer.Overlay
    WlrLayershell.namespace:"violet-pen-ring"
    Item {
        anchors.fill:parent;focus:ring.visible
        Keys.onEscapePressed:ring.controller.penOpened=false
        MouseArea {anchors.fill:parent;onClicked:ring.controller.penOpened=false}
        Item {
            width:360;height:360
            x:Math.max(8,Math.min(parent.width-width-8,ring.controller.penX-(ring.screen ? ring.screen.x : 0)-width/2))
            y:Math.max(8,Math.min(parent.height-height-8,ring.controller.penY-(ring.screen ? ring.screen.y : 0)-height/2))
            Rectangle {anchors.centerIn:parent;width:104;height:104;radius:52;color:"#ee211c2d";border.color:Theme.accent;Text {anchors.centerIn:parent;text:"VIOLET\nKalem";horizontalAlignment:Text.AlignHCenter;color:Theme.accent;font.family:Theme.serif;font.pixelSize:14} MouseArea {anchors.fill:parent;onClicked:ring.controller.penOpened=false}}
            Repeater {
                model:[{name:"Hızlı not",mark:"✎",args:["violet-desktop","quick-note"]},{name:"Ekrana çiz",mark:"⌗",args:["violet-desktop","annotate"]},{name:"Silgi",mark:"◇",args:["violet-desktop","eraser"]},{name:"MyBrain",mark:"✦",args:["mybrain-python"]},{name:"Dosyalar",mark:"▣",args:["nautilus"]},{name:"Komut paleti",mark:"⌕",args:["violet-desktop","palette"]}]
                Rectangle {
                    required property var modelData
                    required property int index
                    width:94;height:76;radius:20
                    x:180+Math.cos((index*60-90)*Math.PI/180)*124-width/2
                    y:180+Math.sin((index*60-90)*Math.PI/180)*124-height/2
                    color:hit.containsMouse ? "#674a87" : "#ee30263f";border.color:hit.containsMouse ? Theme.accent : Theme.border
                    Column {anchors.centerIn:parent;spacing:4;Text {anchors.horizontalCenter:parent.horizontalCenter;text:modelData.mark;color:Theme.accent;font.pixelSize:22} Text {text:modelData.name;color:Theme.pale;font.family:Theme.sans;font.pixelSize:10}}
                    MouseArea {id:hit;anchors.fill:parent;hoverEnabled:true;onClicked:{ring.controller.penOpened=false;ring.controller.command(modelData.args)}}
                }
            }
        }
    }
}
