import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
Item {
    id: dock
    required property var controller
    property var windows: ToplevelManager.toplevels.values
    property string tooltip: ""
    // violet-dock-pins-v3
    property var pins:dock.controller.desktopUi && dock.controller.desktopUi.dockPins!==null && dock.controller.desktopUi.dockPins!==undefined ? dock.controller.desktopUi.dockPins : defaultPins
    property var defaultPins: [
        {name:"MyBrain",icon:"slate",aliases:["mybrain-python"],command:["mybrain-python"]},
        {name:"Firefox",icon:"compass",aliases:["firefox","org.mozilla.firefox"],command:["firefox"]},
        {name:"Terminal",icon:"terminal",aliases:["foot","footclient"],command:["kitty"]},
        {name:"Dosyalar",icon:"folder",aliases:["org.gnome.Nautilus","nautilus"],command:["nautilus"]}
    ]
    function normal(id) { return String(id || "").toLowerCase().replace(/\.desktop$/, ""); }
    function matches(pin) { return windows.filter(w => pin.aliases.map(normal).indexOf(normal(w.appId)) >= 0); }
    function pinned(w) { return pins.some(p => p.aliases.map(normal).indexOf(normal(w.appId)) >= 0); }
    property var others: windows.filter(w => !pinned(w)).slice(0,6)
    implicitWidth: row.implicitWidth + 42
    implicitHeight: 112
    Text {
        anchors.horizontalCenter: parent.horizontalCenter; y: 2
        text: dock.tooltip; color: Theme.pale; font.family: Theme.sans; font.pixelSize: 11
        style: Text.Outline; styleColor: Theme.background
        opacity: dock.tooltip ? 1 : 0
        transform:Translate {y:dock.tooltip ? 0 : 4;Behavior on y {NumberAnimation {duration:Theme.duration(180);easing.type:Easing.OutCubic}}}
        Behavior on opacity { NumberAnimation { duration: Theme.duration(120) } }
    }
    RuneFrame {
        anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.bottomMargin: 12
        height: 78; radius: 24
        Row {
            id: row; anchors.centerIn: parent; spacing: 4
            DockButton { icon:"triforce"; label:"Uygulamalar · Super+D"; active:dock.controller.openPanel==="launcher"; onClicked:dock.controller.toggle("launcher"); onHovered:caption=>dock.tooltip=caption }
            Rectangle { width:1; height:30; color:Theme.border; anchors.verticalCenter:parent.verticalCenter }
            Repeater {
                model: dock.pins
                DockButton {
                    required property var modelData
                    property var targets: dock.matches(modelData)
                    icon: modelData.icon; label: modelData.name
                    iconSource: modelData.iconSource ? Quickshell.iconPath(modelData.iconSource,true) : ""
                    running: targets.length>0
                    active: targets.some(w => w.activated)
                    onHovered: caption=>dock.tooltip=caption
                    onClicked: {
                        if (!targets.length) { dock.controller.command(modelData.command); return; }
                        let index=targets.findIndex(w => w.activated);
                        targets[(index+1)%targets.length].activate();
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
                    onClicked: modelData.activate()
                    onHovered: caption=>dock.tooltip=caption
                }
            }
            Rectangle { width:1; height:30; color:Theme.border; anchors.verticalCenter:parent.verticalCenter }
            DockButton { icon:"music"; label:"Medya"; active:dock.controller.openPanel==="media"; onClicked:(dock.controller.modernTab="media",dock.controller.toggle("modern")); onHovered:caption=>dock.tooltip=caption }
            DockButton { icon:"slate"; label:"Kontrol merkezi · Super+A"; active:dock.controller.openPanel==="dashboard"; onClicked:(dock.controller.modernTab="dashboard",dock.controller.toggle("modern")); onHovered:caption=>dock.tooltip=caption }
        }
    }
}
