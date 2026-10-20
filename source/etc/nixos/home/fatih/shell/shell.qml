import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Services.Pipewire

ShellRoot {
    id:root
    // violet-modern-v1
    property var modern:modernBridge
    property string modernTab:"dashboard"
    ModernBridge {id:modernBridge}
    // kingdom-features-v1
    property var features:kingdom
    property string featureSection:"daily"
    KingdomBridge {id:kingdom}
    // violet-desktop-suite-v2
    // violet-productivity-v3
    property var desktopUi:({})
    property bool recordingActive:false
    property string mediaPlayer:""
    property bool nowPlayingOpen:false
    property bool penOpened:false
    property int penX:0
    property int penY:0
    property bool privateMode:false
    property string openPanel:""
    onOpenPanelChanged:if(privateMode && ["launcher","audio","battery","settings"].indexOf(openPanel)<0) openPanel=""
    onPrivateModeChanged:{Theme.presentationMode=privateMode;if(privateMode){openPanel="";nowPlayingOpen=false;penOpened=false;showWelcome=false}}
    Timer {id:desktopWatchRetry;interval:3000;onTriggered:desktopWatch.running=true}
    Process {
        id:desktopWatch
        onExited:desktopWatchRetry.restart()
        command:["violet-desktop-watch"];running:true
        stdout:SplitParser {onRead:data=>{try {let value=JSON.parse(data);root.privateMode=value.presentation;root.desktopUi=value.ui || {};root.recordingActive=!!value.recording;if(typeof root.desktopUi.motionSpeed==="number") Theme.motionTempo=root.desktopUi.motionSpeed;}catch(e){}}}
    }
    property bool entered:false
    property bool greeted:false
    property bool showWelcome:false
    property var state:({active:"1",title:"Masaüstü",groups:[],brightness:null,battery:null,charging:false,wifi:"Bağlantı bekleniyor",media:"",profile:""})
    property string timeText:Qt.formatDateTime(new Date(),"HH:mm")
    property string dateText:Qt.formatDateTime(new Date(),"dd.MM.yyyy")
    property var audio:Pipewire.defaultAudioSink ? Pipewire.defaultAudioSink.audio : null
    property real volume:audio ? audio.volume*100 : 0
    property bool muted:audio ? audio.muted : false
    property real brightnessPreview:state.brightness || 0
    property bool fullscreen:ToplevelManager.activeToplevel ? ToplevelManager.activeToplevel.fullscreen : false
    function restartWelcome() { welcomeTimer.restart(); }
    function toggle(panel) { openPanel=openPanel===panel ? "" : panel; }
    function command(args) { Quickshell.execDetached(args); }
    function value(n) { return n===null || n===undefined ? "—" : n+"%"; }
    function setVolume(n) { if (audio) audio.volume=Math.max(0,Math.min(1,n/100)); }
    function setBrightness(n) { brightnessPreview=n; brightnessCommit.restart(); }
    Component.onCompleted:Qt.callLater(()=>root.entered=true)
    PwObjectTracker { objects:[Pipewire.defaultAudioSink] }
    Timer { id:brightnessCommit; interval:90; onTriggered:root.command(["brightnessctl","set",String(Math.max(1,Math.round(root.brightnessPreview)))+"%"]) }
    Timer { interval:1000; running:true; repeat:true; onTriggered:{root.timeText=Qt.formatDateTime(new Date(),"HH:mm");root.dateText=Qt.formatDateTime(new Date(),"dd.MM.yyyy");} }
    Process {
        command:["fatih-shell-status","--watch"]; running:true
        stdout:SplitParser {
            onRead:data=>{
                try {
                    root.state=Object.assign({},root.state,JSON.parse(data));
                    if (!brightnessCommit.running) root.brightnessPreview=root.state.brightness || 0;
                    if (!root.greeted && root.state.session) {
                        root.greeted=true;
                        if (root.state.welcome && Theme.welcomeEnabled) {root.showWelcome=true;welcomeTimer.start();}
                    }
                } catch(e) { console.warn("Status:",e); }
            }
        }
    }
    IpcHandler {
        target:"desktop"
        function toggle():void { (root.modernTab="dashboard",root.toggle("modern")); }
        function launcher():void { root.toggle("launcher"); }
        function quit():void { Qt.quit(); }
        function welcome():void { root.openPanel="";root.showWelcome=false;Qt.callLater(()=>{root.showWelcome=true;welcomeTimer.restart();}); }
        function settings():void { root.toggle("settings"); }
        function notifications():void {root.toggle("notifications");}
        function feature(name:string):void {if(!root.privateMode){root.featureSection=name;root.openPanel="features";}}
        // hyrule-shortcut-guide-v1
        function shortcuts():void {root.toggle("shortcuts");}
        function audio():void {root.toggle("audio");}
        function clock():void {root.toggle("clock");}
        function battery():void {root.toggle("battery");}
        function modern(tab:string):void {if(!root.privateMode){root.modernTab=tab;root.openPanel="modern";}}
        function pen(x:int,y:int):void {if(!root.privateMode){root.penX=x;root.penY=y;root.penOpened=!root.penOpened;}}
        function privacy(enabled:string):void {root.privateMode=enabled==="true";}
        function nowPlaying():void {if(!root.privateMode)root.nowPlayingOpen=!root.nowPlayingOpen;}
        function close():void { root.openPanel="";root.nowPlayingOpen=false;root.penOpened=false; }
    }
    Process { command:["mako","--config",Quickshell.shellPath("mako.conf")]; running:true }
    PanelWindow {
        anchors { top:true; bottom:true; left:true; right:true }
        exclusionMode:ExclusionMode.Ignore; color:Theme.background
        WlrLayershell.layer:WlrLayer.Background
        WlrLayershell.namespace:"fatih-hyrule-background"
        Image { anchors.fill:parent; source:kingdom.state.wallpaper || Qt.resolvedUrl("assets/hyrule-violet.png"); fillMode:Image.PreserveAspectCrop }
        Rectangle {
            anchors.fill:parent;color:Theme.ink
            opacity:kingdom.state.scheduled ? (kingdom.state.day ? .02 : .16) : 0
            Behavior on opacity {NumberAnimation {duration:Theme.duration(600)}}
        }
        Column {
            x:54; anchors.bottom:parent.bottom; anchors.bottomMargin:152; spacing:12
            Text { text:"H Y R U L E"; color:Theme.pale; opacity:.8; font.family:Theme.serif; font.pixelSize:30; style:Text.Outline; styleColor:Theme.background }
            Row {
                spacing:10
                Rectangle { width:32; height:1; color:Theme.accent; anchors.verticalCenter:parent.verticalCenter }
                Text { text:"VIOLET  ·  GECE YOLCULUĞU"; color:Theme.accent; font.family:Theme.sans; font.pixelSize:9; font.letterSpacing:2; style:Text.Outline; styleColor:Theme.background }
            }
        }
    }
    PanelWindow {
        anchors { top:true; left:true; right:true }
        implicitHeight:64; exclusiveZone:64; color:"transparent"; visible:!root.fullscreen && !kingdom.state.game
        WlrLayershell.namespace:"fatih-hyrule-top"
        TopBar {
            anchors.fill:parent; controller:root; opacity:root.entered ? 1 : 0
            transform:Translate { y:root.entered ? 0 : -12; Behavior on y { NumberAnimation { duration:Theme.duration(360); easing.type:Easing.OutCubic } } }
            Behavior on opacity { NumberAnimation { duration:Theme.duration(260) } }
        }
    }
    PanelWindow {
        anchors { bottom:true }
        implicitWidth:dock.implicitWidth; implicitHeight:112; exclusiveZone:104
        color:"transparent"; visible:!root.fullscreen && !kingdom.state.game
        WlrLayershell.namespace:"fatih-hyrule-dock"
        BottomDock {
            id:dock; anchors.fill:parent; controller:root; opacity:root.entered ? 1 : 0
            transform:Translate { y:root.entered ? 0 : 18; Behavior on y { NumberAnimation { duration:Theme.duration(380); easing.type:Easing.OutCubic } } }
            Behavior on opacity { NumberAnimation { duration:Theme.duration(280) } }
        }
    }
    NowPlaying {controller:root}
    RadialMenu {controller:root}
    SpiritCompanion {controller:root}
    WindowSwitcher {}
    Popup {opened:root.openPanel==="notifications";onDismissed:root.openPanel="";panelWidth:480;body:Component {NotificationPanel {controller:root}}}
    Launcher { controller:root; opened:root.openPanel==="launcher" }
    Popup {
        opened:root.openPanel==="modern";onDismissed:root.openPanel="";panelWidth:root.modernTab==="buds" ? 540 : 840
        centered:false
        body:Component {ModernDashboard {controller:root}}
    }
    Popup {
        opened:root.openPanel==="shortcuts";onDismissed:root.openPanel="";panelWidth:760
        body:Component {ShortcutGuide {controller:root}}
    }
    Popup {
        opened:root.openPanel==="features";onDismissed:root.openPanel="";panelWidth:800
        body:Component {KingdomPanel {controller:root;bridge:kingdom;section:root.featureSection}}
    }
    Popup {
        opened:root.openPanel==="audio"; onDismissed:root.openPanel=""
        body:Component {
            ColumnLayout {
                spacing:20
                RowLayout { Sigil { width:28;height:28;name:"volume" } Text { text:"Ses";color:Theme.pale;font.family:Theme.serif;font.pixelSize:28 } }
                Text { text:root.audio ? "Varsayılan ses çıkışı" : "Ses çıkışı bulunamadı";color:Theme.muted;font.family:Theme.sans;font.pixelSize:12 }
                Control { Layout.fillWidth:true;label:"Çıkış seviyesi";value:root.volume;onAdjusted:number=>root.setVolume(number) }
                RowLayout { Pill { label:root.muted ? "Sesi aç" : "Sessize al";onClicked:if(root.audio) root.audio.muted=!root.audio.muted } Pill {label:"Aygıtlar";onClicked:{root.featureSection="audio";root.openPanel="features";}} }
            }
        }
    }
    Popup { opened:root.openPanel==="clock";onDismissed:root.openPanel="";body:Component { ClockPanel {} } }
    Popup {
        opened:root.openPanel==="battery";onDismissed:root.openPanel=""
        body:Component {
            ColumnLayout {
                spacing:20
                RowLayout { Sigil { width:28;height:28;name:"heart" } Text { text:"Enerji";color:Theme.pale;font.family:Theme.serif;font.pixelSize:28 } }
                Text { text:root.value(root.state.battery);color:Theme.accent;font.family:Theme.serif;font.pixelSize:64 }
                Text { text:root.state.charging ? "Şarj oluyor" : root.state.battery===null ? "Pil verisi yok" : "Pil kullanımı";color:Theme.muted;font.family:Theme.sans;font.pixelSize:13 }
                Text { text:"Pil sağlığı: "+root.value(root.state.health)+"  ·  Döngü: "+(root.state.cycles || "—");color:Theme.pale;font.family:Theme.sans;font.pixelSize:11 }
                Text { text:root.state.profile ? "Güç profili: "+({"balanced":"Dengeli","power-saver":"Tasarruf","performance":"Performans"}[root.state.profile] || root.state.profile) : "Güç profili verisi bekleniyor";color:Theme.muted;font.family:Theme.sans;font.pixelSize:11 }
                Flow {
                    Layout.fillWidth:true; spacing:6
                    Repeater {
                        model:[{id:"power-saver",name:"Tasarruf"},{id:"balanced",name:"Dengeli"},{id:"performance",name:"Performans"}]
                        Pill { required property var modelData;label:modelData.name;visible:!!root.state.profile;fill:root.state.profile===modelData.id ? "#46385d" : Theme.raised;onClicked:root.command(["powerprofilesctl","set",modelData.id]) }
                    }
                }
            }
        }
    }
    Popup {
        opened:root.openPanel==="media";onDismissed:root.openPanel=""
        body:Component {
            ColumnLayout {
                spacing:20
                RowLayout { Sigil { width:28;height:28;name:"music" } Text { text:"Melodiler";color:Theme.pale;font.family:Theme.serif;font.pixelSize:28 } }
                Text { Layout.fillWidth:true;text:root.state.media || "Henüz bir şey çalmıyor";wrapMode:Text.WordWrap;color:Theme.muted;font.family:Theme.sans;font.pixelSize:13;textFormat:Text.PlainText }
                RowLayout {
                    Pill { label:"‹";onClicked:root.command(["playerctl","previous"]) }
                    Pill { label:root.state.playing ? "Duraklat" : "Oynat";onClicked:root.command(["playerctl","play-pause"]) }
                    Pill { label:"›";onClicked:root.command(["playerctl","next"]) }
                }
            }
        }
    }
    Popup {
        opened:root.openPanel==="dashboard";onDismissed:root.openPanel="";panelWidth:432
        body:Component {
            ColumnLayout {
                spacing:18
                RowLayout {
                    Layout.fillWidth:true
                    ColumnLayout {
                        Layout.fillWidth:true;spacing:5
                        Text { text:"Sheikah Tahtası";color:Theme.pale;font.family:Theme.serif;font.pixelSize:26 }
                        Text { text:"KONTROL MERKEZİ";color:Theme.muted;font.family:Theme.sans;font.pixelSize:9;font.letterSpacing:2 }
                    }
                    Pill { label:"×";onClicked:root.openPanel="" }
                }
                Rectangle {
                    Layout.fillWidth:true;implicitHeight:92;radius:16;clip:true;color:Theme.ink
                    Image { anchors.fill:parent;source:Qt.resolvedUrl("assets/hyrule-violet.png");fillMode:Image.PreserveAspectCrop;opacity:.48 }
                    Rectangle { anchors.fill:parent;color:"#66251a42" }
                    RowLayout {
                        anchors.fill:parent;anchors.margins:17;spacing:15
                        Sigil { width:34;height:34 }
                        ColumnLayout {
                            Layout.fillWidth:true;spacing:5
                            Text { text:"Krallığa hoş geldin, Fatih";color:Theme.pale;font.family:Theme.serif;font.pixelSize:17 }
                            Text { text:"YOGA 7  ·  HYRULE / VIOLET";color:Theme.accent;font.family:Theme.sans;font.pixelSize:8;font.letterSpacing:1 }
                        }
                    }
                }
                RuneFrame {
                    Layout.fillWidth:true;implicitHeight:76;ornament:false;color:Theme.raised;radius:14
                    RowLayout {
                        anchors.fill:parent;anchors.margins:15;spacing:13
                        Sigil { width:24;height:24;name:"wifi" }
                        ColumnLayout {
                            Layout.fillWidth:true;spacing:6
                            Text { text:"KABLOSUZ AĞ";color:Theme.accent;font.family:Theme.sans;font.pixelSize:8;font.letterSpacing:2 }
                            Text { Layout.fillWidth:true;text:root.state.wifi;elide:Text.ElideRight;color:Theme.pale;font.family:Theme.sans;font.pixelSize:13;textFormat:Text.PlainText }
                        }
                    }
                    MouseArea { anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:root.command(["foot","-e","nmtui"]) }
                }
                RowLayout {
                    Layout.fillWidth:true
                    Pill { label:"Bluetooth";Layout.fillWidth:true;onClicked:root.command(["blueman-manager"]) }
                    Pill { label:"Enerji";Layout.fillWidth:true;onClicked:root.toggle("battery") }
                }
                Control { Layout.fillWidth:true;label:"Ses";value:root.volume;onAdjusted:number=>root.setVolume(number) }
                Control { Layout.fillWidth:true;label:"Parlaklık";value:root.brightnessPreview;onAdjusted:number=>root.setBrightness(number) }
                RowLayout {
                    Layout.fillWidth:true
                    Text { Layout.fillWidth:true;text:"Sade hareket";color:Theme.muted;font.family:Theme.sans;font.pixelSize:11 }
                    Pill { label:Theme.reducedMotion ? "Açık" : "Kapalı";onClicked:Theme.reducedMotion=!Theme.reducedMotion }
                }
                Pill { Layout.fillWidth:true;label:"Masaüstü ayarları  ›";onClicked:root.toggle("settings") }
                Pill {Layout.fillWidth:true;label:"Kısayol rehberi  ›";onClicked:root.toggle("shortcuts")}
                Pill {Layout.fillWidth:true;label:"Krallık panelleri  ›";onClicked:{root.featureSection="daily";root.toggle("features");}}
                RuneFrame {
                    Layout.fillWidth:true;implicitHeight:90;radius:14;ornament:false;color:Theme.raised
                    ColumnLayout {
                        anchors.fill:parent;anchors.margins:14;spacing:7
                        Text { text:"ŞİMDİ ÇALIYOR";color:Theme.accent;font.family:Theme.sans;font.pixelSize:8;font.letterSpacing:2 }
                        Text { Layout.fillWidth:true;text:root.state.media || "Henüz bir şey çalmıyor";elide:Text.ElideRight;color:Theme.pale;font.family:Theme.sans;font.pixelSize:12;textFormat:Text.PlainText }
                        Text { text:"Medya panelini aç  ›";color:Theme.muted;font.family:Theme.sans;font.pixelSize:10 }
                    }
                    MouseArea { anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:(root.modernTab="media",root.toggle("modern")) }
                }
            }
        }
    }

    Popup {
        opened:root.openPanel==="settings";onDismissed:root.openPanel="";panelWidth:480
        body:Component { DesktopSettings { controller:root } }
    }
    Timer { id:welcomeTimer;interval:4800;onTriggered:root.showWelcome=false }
    PanelWindow {
        anchors { top:true;bottom:true;left:true;right:true }
        exclusionMode:ExclusionMode.Ignore;color:"transparent";visible:welcomeBody.visible
        focusable:root.showWelcome
        WlrLayershell.layer:WlrLayer.Overlay;WlrLayershell.namespace:"fatih-hyrule-welcome"
        WelcomeScene { id:welcomeBody;anchors.fill:parent;opened:root.showWelcome;onDismissed:root.showWelcome=false }
    }
}
