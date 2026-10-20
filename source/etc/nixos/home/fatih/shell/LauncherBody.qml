import QtQuick
import QtQuick.Layouts
import Quickshell
Item {
    id: launcher
    required property var controller
    property bool opened: false
    property var entries: DesktopEntries.applications.values
    function fold(text) { return String(text || "").replace(/I/g,"ı").replace(/İ/g,"i").toLowerCase(); }
    property var filtered: {
        let words=fold(search.text).trim().split(/\s+/).filter(s=>s.length);
        return entries.filter(e=> {
            let hay=fold(e.name+" "+e.genericName+" "+(e.keywords || []).join(" "));
            return words.every(word=>hay.indexOf(word)>=0);
        }).sort((a,b)=>a.name.localeCompare(b.name));
    }
    function launch(entry) {
        if (!entry) return;
        if (entry.runInTerminal && entry.command && entry.command.length) {
            Quickshell.execDetached({command:["foot","-e"].concat(Array.from(entry.command)),workingDirectory:entry.workingDirectory});
        } else { entry.execute(); }
        controller.openPanel="";
    }
    function move(delta) {
        if (filtered.length) grid.currentIndex=Math.max(0,Math.min(filtered.length-1,grid.currentIndex+delta));
    }
    onOpenedChanged: if (opened) { search.text=""; grid.currentIndex=0; Qt.callLater(()=>search.forceActiveFocus()); }
    onFilteredChanged: grid.currentIndex=0
    RuneFrame {
        anchors.fill: parent; radius: 28
        Rectangle {
            x:16; y:16; width:226; height:parent.height-32; radius:18; clip:true; color:Theme.ink
            Image { anchors.fill:parent; source:Qt.resolvedUrl("assets/hyrule-violet.png"); fillMode:Image.PreserveAspectCrop; horizontalAlignment:Image.AlignRight; opacity:.6 }
            Rectangle { anchors.fill:parent; color:"#74251a42" }
            Sigil { x:24; y:30; width:38; height:38 }
            Text { x:24; y:92; text:"Hyrule\nAtlası"; color:Theme.pale; font.family:Theme.serif; font.pixelSize:34; lineHeight:1.25 }
            Text { x:26; y:195; text:"UYGULAMALAR"; color:Theme.accent; font.family:Theme.sans; font.pixelSize:9; font.letterSpacing:3 }
            Rectangle { x:26; y:223; width:58; height:1; color:Theme.accent; opacity:.65 }
            Column {
                x:26; anchors.bottom:parent.bottom; anchors.bottomMargin:30; spacing:12
                Text { text:"Hoş geldin, Fatih"; color:Theme.pale; font.family:Theme.serif; font.pixelSize:17 }
                Text { text:"↑ ↓  SEÇ   ·   ENTER  AÇ\nESC  KAPAT"; color:Theme.muted; font.family:Theme.sans; font.pixelSize:8; font.letterSpacing:1; lineHeight:1.9 }
            }
        }
        ColumnLayout {
            x:264; y:26; width:parent.width-290; height:parent.height-52; spacing:16
            RowLayout {
                Layout.fillWidth:true
                Text { text:"Bir sonraki adımın"; font.family:Theme.serif; font.pixelSize:23; color:Theme.pale; Layout.fillWidth:true }
                Pill { label:"×"; onClicked:launcher.controller.openPanel="" }
            }
            Rectangle {
                Layout.fillWidth:true; implicitHeight:54; color:Theme.raised; radius:14; border.color:Theme.border
                Sigil { x:15; anchors.verticalCenter:parent.verticalCenter; width:20; height:20; name:"search" }
                TextInput {
                    id:search; objectName:"launcherSearch"
                    x:49; width:parent.width-65; anchors.verticalCenter:parent.verticalCenter
                    color:Theme.pale; selectionColor:Theme.accent; selectedTextColor:Theme.ink
                    font.family:Theme.sans; font.pixelSize:14; clip:true; selectByMouse:true
                    Text { anchors.fill:parent; text:"Uygulama ara…"; color:Theme.dim; font:parent.font; visible:!search.text && !search.preeditText }
                    Keys.onDownPressed: event=>{ launcher.move(2); event.accepted=true; }
                    Keys.onUpPressed: event=>{ launcher.move(-2); event.accepted=true; }
                    Keys.onTabPressed: event=>{ launcher.move(1); event.accepted=true; }
                    Keys.onBacktabPressed: event=>{ launcher.move(-1); event.accepted=true; }
                    Keys.onReturnPressed: launcher.launch(launcher.filtered[grid.currentIndex])
                    Keys.onEnterPressed: launcher.launch(launcher.filtered[grid.currentIndex])
                    Keys.onEscapePressed: launcher.controller.openPanel=""
                }
            }
            RowLayout {
                Layout.fillWidth:true
                Text { text:search.text ? "ARAMA SONUÇLARI" : "UYGULAMA ARŞİVİ"; color:Theme.muted; font.family:Theme.sans; font.pixelSize:9; font.letterSpacing:2; Layout.fillWidth:true }
                Text { text:launcher.filtered.length+" uygulama"; color:Theme.dim; font.family:Theme.sans; font.pixelSize:10 }
            }
            GridView {
                id:grid; objectName:"launcherGrid"
                Layout.fillWidth:true; Layout.fillHeight:true; clip:true; model:launcher.filtered
                cellWidth:width/2; cellHeight:82; boundsBehavior:Flickable.StopAtBounds
                onCurrentIndexChanged: positionViewAtIndex(currentIndex,GridView.Contain)
                delegate:Item {
                    required property var modelData
                    required property int index
                    width:grid.cellWidth; height:grid.cellHeight
                    property real appearing: launcher.opened ? 1 : 0
                    opacity: appearing
                    transform:Translate { y:(1-appearing)*12 }
                    Behavior on appearing {NumberAnimation {duration:Theme.duration(230+Math.min(index,12)*18);easing.type:Easing.OutCubic}}
                    Rectangle {
                        anchors.fill:parent; anchors.rightMargin:8; anchors.bottomMargin:8; radius:13
                        color:index===grid.currentIndex ? "#3b3053" : hit.containsMouse ? "#2c253b" : Theme.raised
                        border.color:index===grid.currentIndex ? Theme.accent : "#30283e"
                        scale:hit.pressed ? .975 : hit.containsMouse && !Theme.reducedMotion ? 1.012 : 1
                        Behavior on scale {NumberAnimation {duration:Theme.duration(150);easing.type:Easing.OutCubic}}
                        ClickRipple {id:appRipple;anchors.fill:parent}
                        Behavior on color { ColorAnimation { duration:Theme.duration(100) } }
                        Image { id:appIcon; x:15; anchors.verticalCenter:parent.verticalCenter; width:31; height:31; source:modelData.icon ? Quickshell.iconPath(modelData.icon,true) : ""; sourceSize:Qt.size(62,62); fillMode:Image.PreserveAspectFit }
                        Sigil { x:15; anchors.verticalCenter:parent.verticalCenter; width:31; height:31; name:"rune"; visible:!appIcon.source || appIcon.status===Image.Error }
                        Column {
                            x:59; anchors.verticalCenter:parent.verticalCenter; width:parent.width-71; spacing:5
                            Text { width:parent.width; text:modelData.name; color:Theme.pale; font.family:Theme.sans; font.pixelSize:12; elide:Text.ElideRight; textFormat:Text.PlainText }
                            Text { width:parent.width; text:modelData.genericName || "Uygulamayı aç"; color:Theme.muted; font.family:Theme.sans; font.pixelSize:9; elide:Text.ElideRight; textFormat:Text.PlainText }
                        }
                        MouseArea { id:hit; anchors.fill:parent; hoverEnabled:true; cursorShape:Qt.PointingHandCursor; onEntered:grid.currentIndex=index;onPressed:mouse=>appRipple.burst(mouse.x,mouse.y); onClicked:launcher.launch(modelData) }
                    }
                }
                Text { anchors.centerIn:parent; text:"Bu aramayla eşleşen uygulama yok."; color:Theme.muted; font.family:Theme.sans; font.pixelSize:13; visible:!launcher.filtered.length }
            }
            Text { text:"Super+Shift+D  ·  Rofi başlatıcı"; color:Theme.dim; font.family:Theme.sans; font.pixelSize:9 }
        }
    }
}
