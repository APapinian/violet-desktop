import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC
import Quickshell
import Quickshell.Io

ColumnLayout {
    id: devices
    property string section: "audio"
    property var state: ({settings:{lid:{},eq:{bands:[0,0,0]}},sinks:[],outputs:[],profiles:[],lid:{},errors:[]})
    property string message: "Denetimler hazırlanıyor…"
    property var jobs: []
    property bool busy: false
    property bool dirty: false
    property int hz: 60
    property var draft: [0,0,0]
    spacing: 13
    function refresh() { if(!poll.running) poll.running=true; }
    function act(action,value) {
        jobs.push({action:action,value:value});next();
    }
    function next() {
        if(busy || !jobs.length)return;
        const job=jobs.shift();busy=true;
        worker.command=["/home/fatih/.local/share/violet-controls/bin/violetctl",job.action,JSON.stringify(job.value===undefined ? null : job.value)];worker.running=true;
    }
    Component.onCompleted:refresh()
    Process {
        id:poll;command:["/home/fatih/.local/share/violet-controls/bin/violetctl","status"]
        stdout:SplitParser {onRead:line=>{
            try {
                const response=JSON.parse(line);
                if(response.ok){devices.state=response.result;if(!devices.busy && !devices.dirty)devices.draft=response.result.settings.eq.bands.slice();}
                else devices.message=response.error;
            }catch(e){devices.message="Durum yanıtı okunamadı";}
        }}
    }
    Process {
        id:worker
        stdout:SplitParser {onRead:line=>{
            try{const response=JSON.parse(line);devices.message=response.ok ? response.result : response.error;}catch(e){devices.message="İşlem yanıtı okunamadı";}
        }}
        onExited:{devices.busy=false;devices.refresh();Qt.callLater(()=>devices.next());}
    }
    Timer {interval:1000;running:devices.visible;repeat:true;onTriggered:devices.refresh()}
    Text {Layout.fillWidth:true;text:devices.busy ? "Uygulanıyor…" : devices.message;color:Theme.accent;font.pixelSize:12;wrapMode:Text.WordWrap;textFormat:Text.PlainText}
    Repeater {model:devices.state.errors || [];Text {required property string modelData;Layout.fillWidth:true;text:modelData;color:"#ffb4ab";wrapMode:Text.WordWrap;font.pixelSize:11;textFormat:Text.PlainText}}
    ColumnLayout {
        visible:devices.section==="audio";Layout.fillWidth:true;spacing:12
        Text {text:"SES ÇIKIŞI";color:Theme.accent;font.pixelSize:11}
        Repeater {
            model:devices.state.sinks || []
            Rectangle {
                required property var modelData
                Layout.fillWidth:true;implicitHeight:sinkRow.implicitHeight+22;radius:16;color:Theme.raised;border.color:Theme.border
                RowLayout {
                    id:sinkRow;anchors.fill:parent;anchors.margins:11
                    Text {Layout.fillWidth:true;text:modelData.description;color:Theme.pale;wrapMode:Text.WordWrap;font.pixelSize:12;textFormat:Text.PlainText}
                    Pill {label:modelData.default || (devices.state.eqActive && devices.state.settings.eq.target===modelData.name) ? "Seçili" : "Seç";enabled:!devices.busy;onClicked:devices.act("sink",modelData.name)}
                }
            }
        }
        Text {Layout.fillWidth:true;text:"AUX hoparlörün adı sistemde Lecoo olarak görünmeyebilir. Fişin bağlı olduğu analog veya HDMI çıkışını seç.";color:Theme.muted;font.pixelSize:11;wrapMode:Text.WordWrap}
        RowLayout {
            Layout.fillWidth:true
            Text {Layout.fillWidth:true;text:"Violet ekolayzır";color:Theme.pale;font.family:Theme.serif;font.pixelSize:23}
            Pill {label:devices.state.eqActive ? "Kapat" : "Aç";enabled:!devices.busy;onClicked:devices.act("eq",!devices.state.eqActive)}
        }
        Flow {Layout.fillWidth:true;spacing:7;Repeater {model:devices.state.profiles || [];Pill {required property string modelData;label:modelData;enabled:!devices.busy;fill:devices.state.settings.eq.profile===modelData && devices.state.eqActive ? "#46385d" : Theme.raised;onClicked:{devices.dirty=false;devices.act("profile",modelData);}}}}
        Text {text:"Profil: "+(devices.state.settings.eq.profile || "Dengeli");color:Theme.muted;font.pixelSize:12}
        Repeater {
            model:["Bas · 120 Hz","Orta · 1,5 kHz","Tiz · 6 kHz"]
            ColumnLayout {
                required property string modelData
                required property int index
                Layout.fillWidth:true;spacing:5
                RowLayout {
                    Layout.fillWidth:true
                    Text {Layout.fillWidth:true;text:modelData;color:Theme.pale;font.pixelSize:13}
                    Text {text:Number(devices.draft[index]).toFixed(1)+" dB";color:Theme.accent;font.pixelSize:13}
                }
                QQC.Slider {
                    id:bandSlider
                    Layout.fillWidth:true;from:-6;to:6;stepSize:.5
                    value:Number(devices.draft[index])
                    onMoved:{let values=devices.draft.slice();values[index]=value;devices.draft=values;devices.dirty=true;}
                    background:Rectangle {
                        x:bandSlider.leftPadding;y:bandSlider.topPadding+bandSlider.availableHeight/2-height/2
                        width:bandSlider.availableWidth;height:5;radius:3;color:Theme.border
                        Rectangle {width:bandSlider.visualPosition*parent.width;height:parent.height;radius:3;color:Theme.accent}
                    }
                    handle:Rectangle {
                        x:bandSlider.leftPadding+bandSlider.visualPosition*(bandSlider.availableWidth-width)
                        y:bandSlider.topPadding+bandSlider.availableHeight/2-height/2
                        width:14;height:14;radius:3;rotation:45;color:Theme.accent
                    }
                }
            }
        }
        Pill {label:"Bantları uygula";enabled:!devices.busy;onClicked:{devices.act("bands",devices.draft);devices.dirty=false;}}
        Text {Layout.fillWidth:true;text:"Bant aralığı −6 / +6 dB. Pozitif kazanç için giriş seviyesi otomatik azaltılır. Profil değişirken seste kısa bir kesinti olabilir.";color:Theme.muted;font.pixelSize:11;wrapMode:Text.WordWrap}
    }
    ColumnLayout {
        visible:devices.section==="display";Layout.fillWidth:true;spacing:12
        Text {text:"EKRANLAR";color:Theme.accent;font.pixelSize:11}
        Repeater {model:devices.state.outputs || [];Text {required property var modelData;Layout.fillWidth:true;text:(modelData.enabled ? "● " : "○ ")+modelData.name+" · "+modelData.description+(modelData.mode ? "\n"+modelData.mode : "");color:Theme.pale;wrapMode:Text.WordWrap;font.pixelSize:12;textFormat:Text.PlainText}}
        RowLayout {
            Text {text:"MSI yenileme hızı";color:Theme.muted;font.pixelSize:12}
            Pill {label:"60 Hz";fill:devices.hz===60 ? "#46385d" : Theme.raised;onClicked:devices.hz=60}
            Pill {label:"120 Hz";fill:devices.hz===120 ? "#46385d" : Theme.raised;onClicked:devices.hz=120}
        }
        Flow {
            Layout.fillWidth:true;spacing:7
            Repeater {model:[{id:"msi",name:"Yalnız MSI"},{id:"laptop",name:"Yalnız laptop"},{id:"dual",name:"İki ayrı masaüstü"}];Pill {required property var modelData;label:modelData.name;enabled:!devices.busy && !devices.state.pending;onClicked:devices.act("display",{layout:modelData.id,hz:devices.hz})}}
        }
        ColumnLayout {
            visible:!!devices.state.pending;Layout.fillWidth:true
            Text {text:"Görüntü düzgün mü? "+(devices.state.pending ? devices.state.pending.seconds : 0)+" saniye";color:Theme.accent;font.pixelSize:16}
            RowLayout {Pill {label:"Bu düzeni koru";enabled:!devices.busy;onClicked:devices.act("confirm")} Pill {label:"Geri dön";enabled:!devices.busy;onClicked:devices.act("rollback")}}
        }
        Text {Layout.fillWidth:true;text:"İki ekranda farklı Qtile grupları açılır. İmleç ekranlar arasında geçebilir. Onaylanmayan ekran düzeni 15 saniye sonra geri alınır. Bağlantının desteklediği 120 Hz modu denenebilir.";color:Theme.muted;font.pixelSize:12;wrapMode:Text.WordWrap}
    }
    ColumnLayout {
        visible:devices.section==="lid";Layout.fillWidth:true;spacing:13
        Text {text:"KAPAK DAVRANIŞI";color:Theme.accent;font.pixelSize:11}
        Text {Layout.fillWidth:true;text:devices.state.lid.ready ? "Kapak denetimi etkin · "+(devices.state.lid.source==="ac" ? "Şarjda" : "Bataryada")+(devices.state.lid.closed ? " · kapalı" : " · açık") : devices.state.lid.error || "Kapak servisi bekleniyor";color:devices.state.lid.ready ? Theme.pale : "#ffb4ab";wrapMode:Text.WordWrap;font.pixelSize:12;textFormat:Text.PlainText}
        Repeater {
            model:[{id:"ac",name:"Şarja bağlıyken"},{id:"battery",name:"Bataryadayken"}]
            ColumnLayout {
                required property var modelData;Layout.fillWidth:true;spacing:8
                Text {text:modelData.name;color:Theme.pale;font.family:Theme.serif;font.pixelSize:20}
                Flow {
                    Layout.fillWidth:true;spacing:7
                    Pill {label:"Kapak kapanınca uyut";enabled:!devices.busy;fill:devices.state.settings.lid[modelData.id]==="suspend" ? "#46385d" : Theme.raised;onClicked:devices.act("lid",{source:modelData.id,mode:"suspend"})}
                    Pill {label:"Monitörle devam et";enabled:!devices.busy;fill:devices.state.settings.lid[modelData.id]==="monitor" ? "#46385d" : Theme.raised;onClicked:devices.act("lid",{source:modelData.id,mode:"monitor"})}
                }
            }
        }
        Text {Layout.fillWidth:true;text:"Monitörle devam et: harici ekran bağlıyken kapak kapanması uyutmaz. Kapak kapalıyken harici monitör çıkarılırsa bilgisayar uyur. Laptop ekranını kapatmak için Ekran → Yalnız MSI seç.";color:Theme.muted;font.pixelSize:12;wrapMode:Text.WordWrap}
    }
}
