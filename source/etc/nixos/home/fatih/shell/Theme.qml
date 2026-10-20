pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
Singleton {
    id: theme
    // violet-presentation-text-v2
    property bool presentationMode:false
    function textSize(value) {return presentationMode ? Math.round(value*1.18) : value;}
    readonly property color background: "#100f18"
    readonly property color surface: "#17151f"
    readonly property color raised: "#251f32"
    readonly property color border: "#463c57"
    readonly property color accent: "#c5b4ff"
    readonly property color pale: "#ece4f8"
    readonly property color muted: "#aaa1ba"
    readonly property color dim: "#736982"
    readonly property color ink: "#251a42"
    readonly property string sans: "Rubik"
    readonly property FontLoader titleFont: FontLoader { source: Qt.resolvedUrl("assets/fonts/DejaVuSerif.ttf") }
    readonly property string serif: titleFont.status === FontLoader.Ready ? titleFont.name : "serif"

    property string motionPreset: "cinematic"
    property bool reducedMotion: false
    property bool ambientEnabled: true
    property bool welcomeEnabled: true
    property real motionTempo: 1
    property real pointerAccel: .2
    property bool naturalScroll: false
    property bool tapToClick: true
    property bool disableWhileTyping: true
    property bool focusFollowsMouse: true
    property int cursorSize: 24
    property string pointerProfile: "adaptive"
    property bool petEnabled: true
    property bool ready: false
    property bool pointerApplyPending: false
    property string saveStatus: ""
    readonly property string stateDir: (Quickshell.env("XDG_STATE_HOME") || (Quickshell.env("HOME") + "/.local/state")) + "/fatih-desktop"
    function duration(ms) {
        if (reducedMotion) return 0;
        const factor = motionPreset === "swift" ? .68 : motionPreset === "cinematic" ? 1.15 : .9;
        return Math.round(ms * factor * motionTempo);
    }
    function snapshot() {
        return {version:1,petEnabled:petEnabled,motionPreset:motionPreset,reducedMotion:reducedMotion,ambientEnabled:ambientEnabled,welcomeEnabled:welcomeEnabled,motionTempo:motionTempo,
            pointerAccel:pointerAccel,naturalScroll:naturalScroll,tapToClick:tapToClick,disableWhileTyping:disableWhileTyping,focusFollowsMouse:focusFollowsMouse,cursorSize:cursorSize,pointerProfile:pointerProfile};
    }
    function restore(data) {
        ready = false;
        if (["swift","balanced","cinematic"].indexOf(data.motionPreset)>=0) motionPreset=data.motionPreset;
        for (let key of ["petEnabled","reducedMotion","ambientEnabled","welcomeEnabled","naturalScroll","tapToClick","disableWhileTyping","focusFollowsMouse"])
            if (typeof data[key] === "boolean") theme[key]=data[key];
        if (typeof data.motionTempo === "number" && isFinite(data.motionTempo)) motionTempo=Math.max(.5,Math.min(1.5,data.motionTempo));
        if (typeof data.pointerAccel === "number" && isFinite(data.pointerAccel)) pointerAccel=Math.max(-1,Math.min(1,data.pointerAccel));
        if ([24,32,40].indexOf(data.cursorSize)>=0) cursorSize=data.cursorSize;
        if (["adaptive","flat"].indexOf(data.pointerProfile)>=0) pointerProfile=data.pointerProfile;
        ready = true;
    }
    function changed() { if (ready) saveTimer.restart(); }
    function saveNow() {
        if (!ready) return;
        saveTimer.stop(); saveStatus="Kaydediliyor";
        preferences.setText(JSON.stringify(snapshot(),null,2)+"\n");
    }
    function applyPointer() { if(!ready){saveStatus="Tercihler hazırlanıyor";return;} pointerApplyPending=true; saveNow(); }
    onPetEnabledChanged: changed()
    onMotionPresetChanged: changed()
    onReducedMotionChanged: changed()
    onAmbientEnabledChanged: changed()
    onWelcomeEnabledChanged: changed()
    onMotionTempoChanged: changed()
    onPointerAccelChanged: changed()
    onNaturalScrollChanged: changed()
    onTapToClickChanged: changed()
    onDisableWhileTypingChanged: changed()
    onFocusFollowsMouseChanged: changed()
    onCursorSizeChanged: changed()
    onPointerProfileChanged: changed()
    Timer { id: saveTimer; interval:400; onTriggered:theme.saveNow() }
    Process {
        command:["mkdir","-p",theme.stateDir]; running:true
        onExited:(exitCode,exitStatus)=>{
            if(exitCode===0) preferences.path=theme.stateDir+"/preferences.json";
            else {theme.ready=false;theme.saveStatus="Tercihler kaydedilemiyor";console.warn("Tercih dizini oluşturulamadı");}
        }
    }
    FileView {
        id:preferences; atomicWrites:true; printErrors:false
        onLoaded:{
            try { theme.restore(JSON.parse(text())); }
            catch(e) { theme.ready=true;theme.saveStatus="Tercih dosyası okunamadı";console.warn("Tercihler:",e); }
        }
        onLoadFailed:theme.ready=true
        onSaved:{
            theme.saveStatus="Kaydedildi";
            if(theme.pointerApplyPending){
                theme.pointerApplyPending=false;
                Quickshell.execDetached(["qtile","cmd-obj","-o","cmd","-f","reload_config"]);
            }
        }
        onSaveFailed:{theme.pointerApplyPending=false;theme.saveStatus="Kaydetme başarısız";console.warn("Masaüstü tercihleri kaydedilemedi");}
    }
}
