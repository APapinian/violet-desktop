import QtQuick
import Quickshell.Io
QtObject {
    id: bridge
    property var state: ({bluetooth:{items:[],buds:{}},cpu:0,memory:0,disk:0,uptime:0})
    property string message: ""
    property var jobs: []
    property bool busy: false
    function call(action,value) { if(action==="player" && value.command==="seek") jobs=jobs.filter(j=>!(j[0]==="player" && j[1].command==="seek")); jobs.push([action,value]); next(); }
    function next() {
        if(busy || !jobs.length)return;
        const j=jobs.shift();busy=true;
        worker.command=["violetctl",j[0],JSON.stringify(j[1])];worker.running=true;
    }
    property Process watcher: Process {
        command:["violetctl","watch"];running:true
        stdout:SplitParser {onRead:line=>{try{bridge.state=JSON.parse(line);}catch(e){console.warn("Violet:",e);}}}
        onExited:retry.restart()
    }
    property Timer retry: Timer {interval:5000;onTriggered:bridge.watcher.running=true}
    property Process worker: Process {
        stdout:SplitParser {onRead:line=>{try{const r=JSON.parse(line);bridge.message=r.ok ? (r.result || "Tamam") : r.error;}catch(e){bridge.message="Yanıt okunamadı";}}}
        onExited:{bridge.busy=false;Qt.callLater(()=>bridge.next());}
    }
}
