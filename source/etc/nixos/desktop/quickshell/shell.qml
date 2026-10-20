import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Services.Pipewire

ShellRoot {
    id: root
    property string openPanel: ''
    property bool entered: false
    property bool greeted: false
    property bool showWelcome: false
    property var state: ({active:'1', title:'Masaüstü', groups:[], brightness:null,
                         battery:null, charging:false, wifi:'Bağlantı bekleniyor', media:'', profile:''})
    property string timeText: Qt.formatDateTime(new Date(), 'HH:mm')
    property string dateText: Qt.formatDateTime(new Date(), 'dd.MM.yyyy')
    property var audio: Pipewire.defaultAudioSink ? Pipewire.defaultAudioSink.audio : null
    property real volume: audio ? audio.volume * 100 : 0
    property bool muted: audio ? audio.muted : false
    property real brightnessPreview: state.brightness || 0
    function toggle(panel) { openPanel = openPanel === panel ? '' : panel; }
    function command(args) { Quickshell.execDetached(args); }
    function value(n) { return n === null || n === undefined ? '—' : n + '%'; }
    function setVolume(n) { if (audio) audio.volume = Math.max(0,Math.min(1,n/100)); }
    function setBrightness(n) { brightnessPreview=n; brightnessCommit.restart(); }
    Component.onCompleted: Qt.callLater(function() { root.entered=true; })
    PwObjectTracker { objects: [Pipewire.defaultAudioSink] }
    Timer {
        id: brightnessCommit; interval: 90
        onTriggered: root.command(['brightnessctl','set',String(Math.max(1,Math.round(root.brightnessPreview)))+'%'])
    }
    Timer {
        interval: 1000; running:true; repeat:true
        onTriggered: {
            root.timeText=Qt.formatDateTime(new Date(),'HH:mm');
            root.dateText=Qt.formatDateTime(new Date(),'dd.MM.yyyy');
        }
    }
    Process {
        id: stats
        command: ['fatih-shell-status','--watch']; running:true
        stdout: SplitParser {
            onRead: data => {
                try {
                    root.state=JSON.parse(data);
                    if (!brightnessCommit.running) root.brightnessPreview=root.state.brightness || 0;
                    if (!root.greeted && root.state.session) {
                        root.greeted=true;
                        if (root.state.welcome) { root.showWelcome=true; welcomeTimer.start(); }
                    }
                } catch(e) { console.warn('Status:',e); }
            }
        }
    }
    IpcHandler {
        target:'desktop'
        function toggle(): void { root.toggle('dashboard'); }
        function quit(): void { Qt.quit(); }
        function welcome(): void { root.showWelcome=true; welcomeTimer.restart(); }
    }
    Process { command:['mako','--config',Quickshell.shellPath('mako.conf')]; running:true }
    PanelWindow {
        anchors { top:true; bottom:true; left:true; right:true }
        exclusionMode:ExclusionMode.Ignore
        WlrLayershell.layer:WlrLayer.Background
        WlrLayershell.namespace:'fatih-background'
        color:'#100f18'
        Image { anchors.fill:parent; source:Qt.resolvedUrl('wallpaper.svg'); fillMode:Image.PreserveAspectCrop }
    }
    PanelWindow {
        anchors { top:true; left:true; right:true }
        implicitHeight:64; exclusiveZone:64; color:'transparent'
        WlrLayershell.namespace:'fatih-panel'
        Rectangle {
            anchors.fill:parent; anchors.margins:10; radius:22
            color:'#17151f'; border.color:'#363041'
            opacity:root.entered ? 1 : 0
            transform:Translate { y:root.entered ? 0 : -20; Behavior on y { NumberAnimation { duration:450; easing.type:Easing.OutCubic } } }
            Behavior on opacity { NumberAnimation { duration:350 } }
            RowLayout {
                anchors.fill:parent; anchors.leftMargin:8; anchors.rightMargin:8; spacing:6
                Pill { label:'✦'; fill:'#c5b4ff'; ink:'#251a42'; horizontalPadding:14; onClicked:root.command(['rofi','-show','drun']) }
                Item {
                    Layout.preferredWidth:338
                    implicitHeight:36
                    Rectangle {
                        width:34; height:36; radius:18; color:'#c5b4ff'
                        x:Math.max(0,Math.min(8,Number(root.state.active)-1))*38
                        Behavior on x { NumberAnimation { duration:320; easing.type:Easing.OutCubic } }
                    }
                    Row {
                        spacing:4
                        Repeater {
                            model:9
                            Pill {
                                required property int index
                                label:String(index+1); implicitWidth:34
                                fill:'transparent'
                                ink:root.state.active===label ? '#251a42' : ((root.state.groups[index] && root.state.groups[index].occupied) ? '#e9e1f5' : '#7e768c')
                                onClicked:root.command(['qtile','cmd-obj','-o','group',label,'-f','toscreen'])
                            }
                        }
                    }
                }
                Text {
                    Layout.fillWidth:true; Layout.minimumWidth:0
                    text:root.state.title || 'Masaüstü'; elide:Text.ElideRight
                    color:'#aaa1ba'; font.family:'Rubik'; font.pixelSize:12
                    horizontalAlignment:Text.AlignHCenter; textFormat:Text.PlainText
                }
                Pill { label:root.timeText; fill:'#30293f'; ink:'#e5d8ff'; onClicked:root.toggle('clock') }
                Pill { label:root.muted ? 'Sessiz' : 'Ses '+Math.round(root.volume)+'%'; onClicked:root.toggle('audio') }
                Pill {
                    label:(root.state.charging ? '↯ ' : '')+root.value(root.state.battery)
                    ink:root.state.battery!==null && root.state.battery<20 ? '#ffb4ab' : '#b8dbbc'
                    onClicked:root.toggle('battery')
                }
                Pill { label:'☷'; fill:root.openPanel==='dashboard' ? '#46385d' : '#262331'; onClicked:root.toggle('dashboard') }
            }
        }
    }
    Popup {
        opened:root.openPanel==='audio'; onDismissed:root.openPanel=''
        body:Component {
            ColumnLayout {
                spacing:18
                Text { text:'Ses'; color:'#ece4f8'; font.family:'Rubik'; font.pixelSize:25 }
                Text { text:root.audio ? 'Varsayılan ses çıkışı' : 'Ses çıkışı bulunamadı'; color:'#a69ab6'; font.family:'Rubik'; font.pixelSize:12 }
                Control { Layout.fillWidth:true; label:'Çıkış seviyesi'; value:root.volume; onAdjusted:number=>root.setVolume(number) }
                RowLayout {
                    Layout.fillWidth:true
                    Pill { label:root.muted ? 'Sesi aç' : 'Sessize al'; onClicked:if(root.audio) root.audio.muted=!root.audio.muted }
                    Pill { label:'Aygıtlar'; onClicked:root.command(['pavucontrol']) }
                }
            }
        }
    }
    Popup {
        opened:root.openPanel==='clock'; onDismissed:root.openPanel=''
        body:Component { ClockPanel {} }
    }
    Popup {
        opened:root.openPanel==='battery'; onDismissed:root.openPanel=''
        body:Component {
            ColumnLayout {
                spacing:18
                Text { text:'Enerji'; color:'#ece4f8'; font.family:'Rubik'; font.pixelSize:25 }
                Text { text:root.value(root.state.battery); color:'#b8dbbc'; font.family:'Rubik'; font.pixelSize:56 }
                Text { text:root.state.charging ? 'Şarj oluyor' : root.state.battery===null ? 'Pil verisi yok' : 'Pil kullanımı'; color:'#a69ab6'; font.family:'Rubik'; font.pixelSize:13 }
                Text { text:'Pil sağlığı: '+root.value(root.state.health)+'   ·   Döngü: '+(root.state.cycles || '—'); color:'#ece4f8'; font.family:'Rubik'; font.pixelSize:12 }
                Text { text:root.state.profile ? 'Güç profili: '+({'balanced':'Dengeli','power-saver':'Tasarruf','performance':'Performans'}[root.state.profile] || root.state.profile) : 'Güç profili servisi etkin değil'; color:'#a69ab6'; font.family:'Rubik'; font.pixelSize:12 }
                Flow {
                    Layout.fillWidth:true; spacing:6
                    Repeater {
                        model:[{id:'power-saver',name:'Tasarruf'},{id:'balanced',name:'Dengeli'},{id:'performance',name:'Performans'}]
                        Pill {
                            required property var modelData
                            label:modelData.name
                            visible:!!root.state.profile
                            fill:root.state.profile===modelData.id ? '#46385d' : '#262331'
                            onClicked:root.command(['powerprofilesctl','set',modelData.id])
                        }
                    }
                }
            }
        }
    }
    Popup {
        opened:root.openPanel==='dashboard'; onDismissed:root.openPanel=''
        panelWidth:440
        body:Component {
            ColumnLayout {
                spacing:20
                RowLayout {
                    Layout.fillWidth:true
                    ColumnLayout {
                        Layout.fillWidth:true; spacing:6
                        Text { text:'Kontrol merkezi'; color:'#ece4f8'; font.family:'Rubik'; font.pixelSize:25 }
                        Text { text:'YOGA 7  /  FATİH'; color:'#a69ab6'; font.family:'Rubik'; font.pixelSize:10; font.letterSpacing:2 }
                    }
                    Pill { label:'×'; onClicked:root.openPanel='' }
                }
                Rectangle {
                    Layout.fillWidth:true; implicitHeight:86; radius:22; color:'#30283e'
                    Column {
                        anchors.fill:parent; anchors.margins:16; spacing:10
                        Text { text:'KABLOSUZ AĞ'; color:'#c5b4ff'; font.family:'Rubik'; font.pixelSize:10; font.letterSpacing:2 }
                        Text { width:parent.width; text:root.state.wifi; elide:Text.ElideRight; color:'#ece4f8'; font.family:'Rubik'; font.pixelSize:16; textFormat:Text.PlainText }
                    }
                    MouseArea { anchors.fill:parent; cursorShape:Qt.PointingHandCursor; onClicked:root.command(['foot','-e','nmtui']) }
                }
                RowLayout {
                    Layout.fillWidth:true
                    Pill { label:'Bluetooth'; Layout.fillWidth:true; onClicked:root.command(['blueman-manager']) }
                    Pill { label:'Enerji'; Layout.fillWidth:true; onClicked:root.toggle('battery') }
                }
                Control { Layout.fillWidth:true; label:'Ses'; value:root.volume; onAdjusted:number=>root.setVolume(number) }
                Control { Layout.fillWidth:true; label:'Parlaklık'; value:root.brightnessPreview; accent:'#f2c5a2'; onAdjusted:number=>root.setBrightness(number) }
                Rectangle {
                    Layout.fillWidth:true; implicitHeight:112; radius:22; color:'#282c30'
                    ColumnLayout {
                        anchors.fill:parent; anchors.margins:16; spacing:10
                        Text { text:'ŞİMDİ ÇALIYOR'; color:'#b8dbbc'; font.family:'Rubik'; font.pixelSize:10; font.letterSpacing:2 }
                        Text { Layout.fillWidth:true; text:root.state.media || 'Henüz bir şey çalmıyor'; elide:Text.ElideRight; color:'#e2eee3'; font.family:'Rubik'; font.pixelSize:13; textFormat:Text.PlainText }
                        Row {
                            spacing:8
                            Pill { label:'‹'; implicitHeight:28; onClicked:root.command(['playerctl','previous']) }
                            Pill { label:root.state.playing ? 'Duraklat' : 'Oynat'; implicitHeight:28; onClicked:root.command(['playerctl','play-pause']) }
                            Pill { label:'›'; implicitHeight:28; onClicked:root.command(['playerctl','next']) }
                        }
                    }
                }
            }
        }
    }
    Timer { id:welcomeTimer; interval:2600; onTriggered:root.showWelcome=false }
    PanelWindow {
        anchors { top:true; bottom:true; left:true; right:true }
        exclusionMode:ExclusionMode.Ignore; color:'transparent'
        visible:welcomeBody.opacity>.001
        WlrLayershell.layer:WlrLayer.Overlay
        WlrLayershell.namespace:'fatih-welcome'
        Rectangle {
            id:welcomeBody; anchors.fill:parent; color:'#ef100f18'
            opacity:root.showWelcome ? 1 : 0
            Behavior on opacity { NumberAnimation { duration:550; easing.type:Easing.InOutCubic } }
            MouseArea { anchors.fill:parent; onClicked:root.showWelcome=false }
            Column {
                anchors.centerIn:parent; spacing:22
                scale:root.showWelcome ? 1 : .94
                Behavior on scale { NumberAnimation { duration:700; easing.type:Easing.OutCubic } }
                Item {
                    width:80; height:80; anchors.horizontalCenter:parent.horizontalCenter
                    Rectangle {
                        anchors.fill:parent; radius:40; color:'transparent'; border.width:1; border.color:'#463c57'
                    }
                    Text {
                        anchors.centerIn:parent; text:'✦'; color:'#c5b4ff'; font.pixelSize:46
                        NumberAnimation on rotation { from:0; to:180; duration:2200; running:root.showWelcome; easing.type:Easing.InOutCubic }
                    }
                }
                Text { text:'Hoş geldin, Fatih'; color:'#ece4f8'; font.family:'Rubik'; font.pixelSize:40; anchors.horizontalCenter:parent.horizontalCenter }
                Text { text:'BUGÜN SENİNLE BAŞLIYOR'; color:'#a69ab6'; font.family:'Rubik'; font.pixelSize:11; font.letterSpacing:4; anchors.horizontalCenter:parent.horizontalCenter }
                Rectangle {
                    width:root.showWelcome ? 260 : 0; height:2; radius:1; color:'#c5b4ff'
                    anchors.horizontalCenter:parent.horizontalCenter
                    Behavior on width { NumberAnimation { duration:2000; easing.type:Easing.InOutCubic } }
                }
            }
        }
    }
}
