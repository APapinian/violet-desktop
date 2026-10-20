import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Io

PanelWindow {
    id: switcher
    property var state: ({active:false,rows:[]})
    onStateChanged:Qt.callLater(()=>{let rows=state.rows || [];let index=rows.findIndex(r=>r.selected);viewport.contentY=Math.max(0,Math.min(viewport.contentHeight-viewport.height,index*70-viewport.height/2+31));})
    visible: !!state.active
    screen:Quickshell.screens.find(s=>s.x===state.x && s.y===state.y) || Quickshell.screens[0]
    anchors { top:true;bottom:true;left:true;right:true }
    exclusionMode:ExclusionMode.Ignore;focusable:false;color:"transparent"
    WlrLayershell.layer:WlrLayer.Overlay
    WlrLayershell.namespace:"violet-alt-tab"
    FileView {
        id:source
        path:(Quickshell.env("XDG_RUNTIME_DIR") || "/run/user/1000")+"/fatih-switcher.json"
        watchChanges:true;printErrors:false
        onFileChanged:reload()
        onLoaded:{try {switcher.state=JSON.parse(text());}catch(e){switcher.state=({active:false,rows:[]});}}
    }
    Rectangle {
        anchors.centerIn:parent;width:Math.min(parent.width-48,780);height:Math.min(cards.implicitHeight+92,parent.height-60)
        radius:32;color:"#f2181422";border.color:"#796090"
        ColumnLayout {
            anchors.fill:parent;anchors.margins:24;spacing:16
            Text {text:"Açık pencereler";font.family:Theme.serif;font.pixelSize:24;color:Theme.pale}
            Flickable {
                id:viewport
                Layout.fillWidth:true;Layout.fillHeight:true;contentHeight:cards.implicitHeight;clip:true
                Column {
                    id:cards;width:parent.width;spacing:8
                    Repeater {
                        model:switcher.state.rows || []
                        Rectangle {
                            required property var modelData
                            width:cards.width;height:62;radius:18
                            color:modelData.selected ? "#5c3e74" : "#282132"
                            border.color:modelData.selected ? Theme.accent : "transparent"
                            RowLayout {
                                anchors.fill:parent;anchors.margins:14;spacing:16
                                Text {text:modelData.selected ? "◆" : "◇";color:Theme.accent;font.pixelSize:22}
                                Text {Layout.fillWidth:true;text:modelData.title;textFormat:Text.PlainText;color:Theme.pale;font.pixelSize:13;elide:Text.ElideRight}
                                Text {text:modelData.group;color:Theme.muted;font.pixelSize:11;textFormat:Text.PlainText}
                            }
                        }
                    }
                }
            }
            Text {text:"Tab  İlerle  ·  Shift+Tab  Geri  ·  Alt’ı bırak  Seç";color:Theme.muted;font.pixelSize:10}
        }
    }
}
