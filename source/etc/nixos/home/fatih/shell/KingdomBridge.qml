import QtQuick
import Quickshell
import Quickshell.Io

QtObject {
    id: bridge
    property var state: ({providers:{},pomodoro:{},tablet:{},network:{},queue:[],upcoming:[],headlines:[],later:[],tasks:[],goals:[],notes:"",lyrics:{},usage:{}})
    property var results: []
    property string message: "Veri servisi bekleniyor"
    property bool busy: false
    property string activeAction: ""
    property var requests: []
    property var pendingVolume:null
    property var modelCache:({})
    function stable(previous, next) {
        if(previous===next) return previous;
        if(previous===null || next===null || typeof previous!=="object" || typeof next!=="object" || Array.isArray(previous)!==Array.isArray(next))return next;
        const keys=Object.keys(next);let same=keys.length===Object.keys(previous).length;
        for(const key of keys){next[key]=stable(previous[key],next[key]);if(previous[key]!==next[key])same=false;}
        return same ? previous : next;
    }
    function model(key, values) {
        const result=stable(modelCache[key],values);modelCache[key]=result;return result;
    }
    signal completed(string action, var result)
    function provider(name) { return state.providers[name] || {data:null,status:"waiting",error:"Veri bekleniyor",updated:0}; }
    function data(name) { return provider(name).data || {}; }
    function call(action, value) {
        if(action==="volume") {pendingVolume=value;volumeTimer.restart();return;}
        requests.push({action:action,value:value});
        if (!busy) next();
    }
    function next() {
        if (!requests.length) return;
        const job=requests.shift(); busy=true; activeAction=job.action; message="İşleniyor…";
        worker.command=job.value === undefined ? ["kingdomctl",job.action] : ["kingdomctl",job.action,JSON.stringify(job.value)];
        worker.running=true;
    }
    property Process watcher: Process {
        command: ["kingdomctl","watch"]; running: true
        stdout: SplitParser {
            onRead: line=>{
                try {
                    const parsed=JSON.parse(line);
                    if (parsed.version===1) { bridge.state=bridge.stable(bridge.state,parsed); if(bridge.message==="Veri servisi bekleniyor") bridge.message="Hazır"; }
                    else if(parsed.error) bridge.message=parsed.error;
                } catch(e) {console.warn("Kingdom state:",e);}
            }
        }
        onExited: retry.restart()
    }
    property Timer retry: Timer { interval:5000;onTriggered:bridge.watcher.running=true }
    property Process worker: Process {
        stdout: SplitParser {
            onRead: line=>{
                try {
                    const response=JSON.parse(line);
                    if (response.ok) {
                        bridge.results=response.result;
                        bridge.message=typeof response.result==="string" ? response.result : "Hazır";
                        bridge.completed(bridge.activeAction,response.result);
                    } else bridge.message=response.error || "İşlem tamamlanamadı";
                } catch(e) {bridge.message="Yanıt okunamadı";}
            }
        }
        onExited: {bridge.busy=false;Qt.callLater(()=>bridge.next());}
    }
    property Process volumeWorker: Process {
        onExited:if(bridge.pendingVolume!==null)bridge.volumeTimer.restart()
    }
    property Timer volumeTimer: Timer {
        interval:90
        onTriggered: {
            if(bridge.volumeWorker.running){restart();return;}
            bridge.volumeWorker.command=["kingdomctl","volume",JSON.stringify(bridge.pendingVolume)];
            bridge.pendingVolume=null;bridge.volumeWorker.running=true;
        }
    }
}
