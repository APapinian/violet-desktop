import QtQuick
import QtQuick.Layouts

Item {
    id: topBar
    objectName: "violetTopBar"
    required property var controller
    property var defaultOrder: ["media","dashboard","center","buds","audio","battery","clock"]
    property var order: controller.desktopUi && controller.desktopUi.panelOrder ? controller.desktopUi.panelOrder : defaultOrder
    function open(tab) { controller.modernTab=tab; controller.toggle("modern"); }
    function tool(name) { return ({media:mediaTool,dashboard:dashboardTool,center:centerTool,buds:budsTool,audio:audioTool,battery:batteryTool,clock:clockTool})[name] || null; }

    Rectangle {
        id: ribbon
        anchors.fill: parent; anchors.margins: 9
        radius: 14; color: "#f017151f"; border.color: "#554565"
        Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.leftMargin: 18; anchors.rightMargin: 18; height: 1; color: "#40c5b4ff" }
        Row {
            anchors.left: parent.left; anchors.leftMargin: 14
            anchors.verticalCenter: parent.verticalCenter; spacing: 10
            Sigil {
                width: 22; height: 22; anchors.verticalCenter: parent.verticalCenter
                MouseArea { anchors.fill: parent; anchors.margins: -5; cursorShape: Qt.PointingHandCursor; onClicked: topBar.controller.command(["violet-desktop","palette"]) }
            }
            Text { text: "VIOLET"; color: Theme.accent; font.family: Theme.serif; font.pixelSize: 13; font.letterSpacing: 2; anchors.verticalCenter: parent.verticalCenter }
            Text {
                visible: topBar.width>=1250; width: Math.min(150,topBar.width*.1)
                anchors.verticalCenter: parent.verticalCenter
                text: topBar.controller.privateMode ? "Sunum modu" : topBar.controller.state.application || "Masaüstü"
                color: Theme.muted; font.pixelSize: Theme.textSize(10); elide: Text.ElideRight; textFormat: Text.PlainText
            }
        }
        Row {
            id: workspaces
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter; spacing: 3
            Repeater {
                model: 9
                Rectangle {
                    required property int index
                    property var group: topBar.controller.state.groups.find(g=>g.name===String(index+1)) || ({})
                    property bool selected: topBar.controller.state.active===String(index+1)
                    width: topBar.width<1100 ? 24 : 30; height: 29; radius: 9
                    color: selected ? "#53406d" : hit.containsMouse ? "#30263f" : "transparent"
                    border.color: selected ? "#80709d" : "transparent"
                    Behavior on color { ColorAnimation { duration: Theme.duration(140) } }
                    Text { anchors.centerIn: parent; text: ["I","II","III","IV","V","VI","VII","VIII","IX"][index]; color: parent.selected ? Theme.pale : Theme.muted; font.family: Theme.serif; font.pixelSize: Theme.textSize(10) }
                    Rectangle { anchors.bottom: parent.bottom; anchors.bottomMargin: 3; anchors.horizontalCenter: parent.horizontalCenter; width: 3; height: 3; radius: 2; color: Theme.accent; visible: !!parent.group.occupied && !parent.selected }
                    MouseArea { id: hit; anchors.fill: parent; hoverEnabled: true; onClicked: topBar.controller.command(["qtile","cmd-obj","-o","group",String(index+1),"-f","toscreen"]) }
                }
            }
        }
        RowLayout {
            id: tools
            anchors.right: parent.right; anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter; spacing: topBar.width<1100 ? 4 : 7
            Text { visible: topBar.controller.recordingActive; text: "●"; color: "#ff718c"; font.pixelSize: 14; MouseArea { anchors.fill: parent; onClicked: topBar.controller.command(["violet-desktop","recording"]) } }
            Text {
                Layout.maximumWidth: Math.max(0,Math.min(125,topBar.width-1570)); visible: topBar.width>=1650 && !topBar.controller.privateMode
                text: (topBar.controller.features.data("media").current || {}).title || "Melodiler"
                color: Theme.muted; font.pixelSize: 10; elide: Text.ElideRight; textFormat: Text.PlainText
                MouseArea { anchors.fill: parent; onClicked: topBar.open("media") }
            }
            Repeater {
                model: topBar.order
                Loader {
                    required property string modelData
                    objectName: "violetTool-"+modelData
                    sourceComponent: topBar.tool(modelData)
                    visible: topBar.width>=1050 || ["center","dashboard"].indexOf(modelData)<0
                    Layout.preferredWidth: visible && item ? item.implicitWidth : 0
                    Layout.preferredHeight: 32
                }
            }
            Pill {label:"♧";implicitHeight:32;onClicked:topBar.controller.toggle("notifications")}
            Text { visible: topBar.width>=1750; text: topBar.controller.dateText; color: Theme.dim; font.pixelSize: 10 }
        }
    }
    Component { id: mediaTool; Pill { label: "♪"; implicitHeight: 32; horizontalPadding: 11; onClicked: topBar.open("media") } }
    Component { id: dashboardTool; Pill { label: "◈"; implicitHeight: 32; horizontalPadding: 11; onClicked: topBar.controller.privateMode ? topBar.controller.command(["violet-desktop","presentation"]) : topBar.open("dashboard") } }
    Component { id: centerTool; Pill { label: "▦"; implicitHeight: 32; horizontalPadding: 11; onClicked: topBar.controller.toggle("modern") } }
    Component {
        id: budsTool
        Pill {
            property var buds: topBar.controller.modern.state.bluetooth.buds || ({})
            property var charges: [buds.left,buds.right].filter(x=>x!==null && x!==undefined)
            property var battery: charges.length ? Math.min(...charges) : buds.battery
            label: "Buds"+(buds.connected && battery!==null && battery!==undefined ? " "+battery+"%" : "")
            implicitHeight: 32; horizontalPadding: 11; onClicked: topBar.open("buds")
        }
    }
    Component {
        id: audioTool
        Item {
            implicitWidth: 43; implicitHeight: 32
            Text { anchors.centerIn: parent; text: topBar.controller.muted ? "♪ ×" : "♪ "+Math.round(topBar.controller.volume); color: Theme.pale; font.pixelSize: 10 }
            MouseArea { anchors.fill: parent; onClicked: topBar.controller.toggle("audio"); onWheel: wheel=>{topBar.controller.setVolume(topBar.controller.volume+(wheel.angleDelta.y>0 ? 3 : -3));wheel.accepted=true;} }
        }
    }
    Component { id: batteryTool; Text { text: (topBar.controller.state.charging ? "↯ " : "")+topBar.controller.value(topBar.controller.state.battery); color: Theme.accent; font.pixelSize: 10; MouseArea { anchors.fill: parent; anchors.margins: -5; onClicked: topBar.controller.toggle("battery") } } }
    Component { id: clockTool; Pill { label: topBar.controller.timeText; implicitHeight: 32; horizontalPadding: 12; onClicked: topBar.controller.toggle("clock") } }
}
