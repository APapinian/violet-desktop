import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
Item {
    id: dock
    required property var controller
    // VIOLET_DOCK_V5
    property var targetScreen:null


    readonly property string selectedGroup:controller.outputGroup(targetScreen)
    readonly property bool nativeInventory:controller.state.violetWorkspaces===5
    property var windows:nativeInventory ? (controller.state.windows || []).filter(w=>String(w.group)===selectedGroup) : []
    function activateWindow(window) {
        controller.command([controller.violetCtl,"window-focus",JSON.stringify({id:window.id,group:window.group})]);
    }
    function openPanel(name) {controller.selectOutput(targetScreen);controller.toggle(name);}
    function launch(args) {
        controller.command([controller.violetCtl,"launch",JSON.stringify({output:targetScreen.name,command:args})]);
    }
    property string tooltip: ""
    property var pins: [
        {name:"Firefox",icon:"compass",aliases:["firefox","org.mozilla.firefox"],command:["firefox","--new-window"]},
        {name:"Terminal",icon:"terminal",aliases:["foot","footclient"],command:["foot"]},
        {name:"Dosyalar",icon:"folder",aliases:["org.kde.dolphin","dolphin"],command:["dolphin"]}
    ]
    function normal(id) { return String(id || "").toLowerCase().replace(/\.desktop$/, ""); }
    function matches(pin) { return windows.filter(w => [w.appId].concat(w.classes || []).some(id=>pin.aliases.indexOf(normal(id))>=0)); }
    function pinned(w) { return pins.some(p => [w.appId].concat(w.classes || []).some(id=>p.aliases.indexOf(normal(id))>=0)); }
    property var others: windows.filter(w => !pinned(w)).slice(0,6)
    implicitWidth: row.implicitWidth + 42
    implicitHeight: 112
    Text {
        anchors.horizontalCenter: parent.horizontalCenter; y: 2
        text: dock.tooltip || (dock.targetScreen ? dock.targetScreen.name+"  ·  Masaüstü "+dock.selectedGroup : ""); color: Theme.pale; font.family: Theme.sans; font.pixelSize: 11
        style: Text.Outline; styleColor: Theme.background
        opacity: dock.tooltip ? 1 : .6
        transform:Translate {y:0;Behavior on y {NumberAnimation {duration:Theme.duration(180);easing.type:Easing.OutCubic}}}
        Behavior on opacity { NumberAnimation { duration: Theme.duration(120) } }
    }
    RuneFrame {
        anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.bottomMargin: 12
        height: 78; radius: 24
        Row {
            id: row; anchors.centerIn: parent; spacing: 4
            DockButton { icon:"triforce"; label:"Uygulamalar · Super+D"; active:dock.controller.openPanel==="launcher"; onClicked:dock.openPanel("launcher"); onHovered:caption=>dock.tooltip=caption }
            Rectangle { width:1; height:30; color:Theme.border; anchors.verticalCenter:parent.verticalCenter }
            Repeater {
                model: dock.pins
                DockButton {
                    required property var modelData
                    property var targets: dock.matches(modelData)
                    icon: modelData.icon; label: modelData.name+" · "+(targets.length ? targets.length+" pencere" : "Burada aç")
                    running: targets.length>0
                    active: targets.some(w => w.activated)
                    onHovered: caption=>dock.tooltip=caption
                    onClicked: {
                        if (!targets.length) { dock.launch(modelData.command); return; }
                        let index=targets.findIndex(w => w.activated);
                        dock.activateWindow(targets[(index+1)%targets.length]);
                    }
                }
            }
            Repeater {
                model: dock.others
                DockButton {
                    required property var modelData
                    property var entry: DesktopEntries.byId(modelData.appId)
                    iconSource: entry && entry.icon ? Quickshell.iconPath(entry.icon,true) : ""
                    icon: "rune"; label: modelData.title || modelData.appId
                    running: true; active: modelData.activated
                    onClicked: dock.activateWindow(modelData)
                    onHovered: caption=>dock.tooltip=caption
                }
            }
            Rectangle { width:1; height:30; color:Theme.border; anchors.verticalCenter:parent.verticalCenter }
            DockButton { icon:"music"; label:"Medya"; active:dock.controller.openPanel==="media"; onClicked:dock.openPanel("media"); onHovered:caption=>dock.tooltip=caption }
            DockButton { icon:"slate"; label:"Kontrol merkezi · Super+A"; active:dock.controller.openPanel==="dashboard"; onClicked:dock.openPanel("dashboard"); onHovered:caption=>dock.tooltip=caption }
        }
    }
}
