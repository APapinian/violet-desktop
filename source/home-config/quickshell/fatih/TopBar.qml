import QtQuick
import QtQuick.Layouts
Item {
    id: topBar
    required property var controller
    // VIOLET_TOPBAR_V5
    property var targetScreen:null
    readonly property string selectedGroup:controller.outputGroup(targetScreen)
    readonly property var screenState:controller.outputState(targetScreen)
    readonly property int cellWidth:width<1150 ? 30 : 38
    readonly property var groupNames:["Kod","Web","Hukuk","Okuma","Medya","Sohbet","Sistem","8","9"]
    readonly property string groupName:groupNames[Number(selectedGroup)-1] || selectedGroup


    RuneFrame {
        x:216;y:11;width:Math.max(100,topBar.width/2-428);height:48
        visible:topBar.width>=1450
        Column {
            anchors.fill:parent;anchors.margins:10;spacing:3
            Text {
                text:(topBar.targetScreen ? topBar.targetScreen.name : "Ekran")+"  ·  "+topBar.groupName
                color:Theme.accent;font.family:Theme.sans;font.pixelSize:9
            }
            Text {
                width:parent.width;text:topBar.screenState ? topBar.screenState.title : "Masaüstü"
                textFormat:Text.PlainText;elide:Text.ElideRight
                color:Theme.pale;font.family:Theme.sans;font.pixelSize:11
            }
        }
    }
    property real wheelVolume:controller.volume
    Timer {id:volumeCommit;interval:100;onTriggered:topBar.controller.features.call("volume",topBar.wheelVolume/100)}
    RuneFrame {
        x: 18; y: 11; width: topBar.width < 1150 ? 148 : 184; height: 48
        Row {
            anchors.centerIn: parent; spacing: 13
            Sigil { width: 30; height: 30; anchors.verticalCenter: parent.verticalCenter }
            Column {
                spacing: 3
                Text { text: "HYRULE"; color: Theme.pale; font.family: Theme.serif; font.pixelSize: 17; font.letterSpacing: 3 }
                Text { text: (topBar.targetScreen ? topBar.targetScreen.name : "VIOLET")+"  ·  "+topBar.groupName; color: Theme.muted; font.family: Theme.sans; font.pixelSize: 8; font.letterSpacing: 2; visible: topBar.width >= 1150 }
            }
        }
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked:{topBar.controller.selectOutput(topBar.targetScreen);topBar.controller.toggle("launcher");} }
    }
    RuneFrame {
        id: workspaces; anchors.horizontalCenter: parent.horizontalCenter; y: 11
        width: 18+9*(topBar.cellWidth+2); height: 48
        Rectangle {
            x: 10 + Math.max(0,Math.min(8,Number(topBar.selectedGroup)-1))*(topBar.cellWidth+2)
            y: 7; width: topBar.cellWidth; height: 34; radius: 10
            color: "#3b3053"; border.color: "#8c77b3"
            Behavior on x { NumberAnimation { duration: Theme.duration(260); easing.type: Easing.OutCubic } }
        }
        Row {
            x: 10; y: 7; spacing: 2
            Repeater {
                model: ["I","II","III","IV","V","VI","VII","VIII","IX"]
                Item {
                    required property int index
                    required property string modelData
                    width: topBar.cellWidth; height: 34
                    scale: workspaceHit.pressed ? .91 : workspaceHit.containsMouse && !Theme.reducedMotion ? 1.06 : 1
                    Behavior on scale { NumberAnimation {duration:Theme.duration(180);easing.type:Easing.OutCubic} }
                    property bool selected: topBar.selectedGroup === String(index+1)
                    Text {
                        anchors.centerIn: parent; text: modelData; font.family: Theme.serif; font.pixelSize: 13
                        Behavior on color {ColorAnimation {duration:Theme.duration(180)}}
                        color: parent.selected ? Theme.accent : (topBar.controller.state.groups[index] && topBar.controller.state.groups[index].occupied ? Theme.pale : Theme.dim)
                    }
                    Rectangle { width: 3; height: 3; rotation: 45; color: Theme.accent; anchors.horizontalCenter: parent.horizontalCenter; y: 28; visible: !!(topBar.controller.state.groups[index] && topBar.controller.state.groups[index].occupied) && !groupIcon.visible }
                    Sigil {
                        id:groupIcon;width:10;height:10;y:24;anchors.horizontalCenter:parent.horizontalCenter
                        property string labels:String((topBar.controller.state.groups[index] || {}).label || "")
                        visible:labels.indexOf("  ")>=0
                        name:labels.indexOf("󰈹")>=0 ? "compass" : labels.indexOf("")>=0 ? "terminal" : labels.indexOf("󰎆")>=0 ? "music" : labels.indexOf("󰨞")>=0 ? "slate" : "rune"
                    }
                    Rectangle {
                        width:12;height:2;radius:1;y:2;anchors.horizontalCenter:parent.horizontalCenter
                        color:Theme.muted
                        visible:!parent.selected && (topBar.controller.state.screens || []).some(s=>String(s.group)===String(index+1))
                    }
                    ClickRipple { id:workspaceRipple;anchors.fill:parent }
                    MouseArea { id:workspaceHit;hoverEnabled:true;onPressed:mouse=>workspaceRipple.burst(mouse.x,mouse.y);anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked:{topBar.controller.panelScreen=topBar.targetScreen;topBar.controller.command([topBar.controller.violetCtl,"group",JSON.stringify({output:topBar.targetScreen.name,group:String(index+1)})]);} }
                }
            }
        }
    }
    RuneFrame {
        anchors.right: parent.right; anchors.rightMargin: 18; y: 11; width: topBar.width<1150 ? 302 : 346; height: 48
        RowLayout {
            anchors.fill: parent; anchors.leftMargin: 14; anchors.rightMargin: 12; spacing: 8
            Item {
                Layout.preferredWidth: 77; Layout.fillHeight: true
                Column {
                    anchors.centerIn: parent; spacing: 1
                    Text { text: topBar.controller.timeText; color: Theme.pale; font.family: Theme.sans; font.pixelSize: 15; anchors.horizontalCenter: parent.horizontalCenter }
                    Text { text: topBar.controller.dateText; color: Theme.muted; font.family: Theme.sans; font.pixelSize: 8; anchors.horizontalCenter: parent.horizontalCenter }
                }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked:{topBar.controller.selectOutput(topBar.targetScreen);topBar.controller.toggle("clock");} }
            }
            Rectangle { width: 1; height: 20; color: Theme.border }
            Item {
                Layout.preferredWidth: 64; Layout.fillHeight: true
                Row { anchors.centerIn: parent; spacing: 6; Sigil { width: 17; height: 17; name: topBar.controller.muted ? "mute" : "volume" } Text { text: topBar.controller.muted ? "—" : Math.round(topBar.controller.volume); color: Theme.pale; font.family: Theme.sans; font.pixelSize: 12 } }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked:{topBar.controller.selectOutput(topBar.targetScreen);topBar.controller.toggle("audio");} onWheel:wheel=>{
        topBar.wheelVolume=Math.max(0,Math.min(100,(volumeCommit.running ? topBar.wheelVolume : topBar.controller.volume)+(wheel.angleDelta.y>0 ? 3 : -3)));
        volumeCommit.restart();wheel.accepted=true;
    } }
            }
            Item {
                Layout.preferredWidth: topBar.width<1150 ? 68 : 90; Layout.fillHeight: true
                Row {
                    anchors.centerIn: parent; spacing: 7
                    Sigil { width: 17; height: 17; name: "heart"; opacity: topBar.controller.state.battery !== null && topBar.controller.state.battery<20 ? .55 : 1 }
                    Text { text: (topBar.controller.state.charging ? "↯ " : "") + topBar.controller.value(topBar.controller.state.battery); color: Theme.accent; font.family: Theme.sans; font.pixelSize: 12 }
                }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked:{topBar.controller.selectOutput(topBar.targetScreen);topBar.controller.toggle("battery");} }
            }
            Rectangle { width: 1; height: 20; color: Theme.border }
            Item {
                Layout.preferredWidth: 30; Layout.fillHeight: true
                Sigil { anchors.centerIn: parent; width: 23; height: 23; name: "slate" }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked:{topBar.controller.selectOutput(topBar.targetScreen);topBar.controller.toggle("dashboard");} }
            }
        }
    }
}
