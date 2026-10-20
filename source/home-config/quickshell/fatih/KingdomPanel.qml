import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC
import Quickshell

ColumnLayout {
    id: panel
    required property var controller
    required property var bridge
    property string section: "daily"
    property var searchResults: []
    property string draft: ""
    property string confirmPower: ""
    property var cities: []
    property var sinks: []
    property var clipboard: []
    property string calculation: ""
    spacing: 15
    function rows(name) {return bridge.data(name).items || [];}
    function status(name) {
        const p=bridge.provider(name);
        if(p.status!=="ready") return p.error || "Veri bekleniyor";
        return "Güncellendi: "+Qt.formatDateTime(new Date(p.updated*1000),"HH:mm");
    }
    function change(name) {
        controller.featureSection=name;
    }
    onSectionChanged: {
        searchResults=[];confirmPower="";
        if(section==="clipboard")bridge.call("clipboard");
        if(section==="settings")bridge.call("settings");
        if(section==="notes")note.text=bridge.state.notes;
    }
    Component.onCompleted: {
        if(section==="settings")bridge.call("settings");
        if(section==="clipboard")bridge.call("clipboard");
        note.text=bridge.state.notes;
    }
    Connections {
        target:panel.bridge
        function onCompleted(action,result) {
            if(action==="search-music" || action==="search-video") panel.searchResults=result;
            if(action==="settings") settingsEditor.text=JSON.stringify(result,null,2);
            if(action==="geocode")panel.cities=result;
            if(action==="location") {
                panel.bridge.message="Konum kaydedildi";
                try {let prefs=JSON.parse(settingsEditor.text);prefs.location=result;settingsEditor.text=JSON.stringify(prefs,null,2);}catch(e){panel.bridge.call("settings");}
            }
            if(action==="audio-sinks")panel.sinks=result;
            if(action==="clipboard")panel.clipboard=result;
            if(action==="calculate")panel.calculation=result;
            if(action==="radio-search")panel.searchResults=result.map(e=>({title:e.name,url:e.url_resolved || e.url,artist:e.tags}));
        }
    }
    RowLayout {
        Layout.fillWidth:true
        ColumnLayout {
            Layout.fillWidth:true
            Text {text:"Krallığın akışı";color:Theme.pale;font.family:Theme.serif;font.pixelSize:28}
            Text {text:"HYRULE · VIOLET  /  "+(panel.bridge.state.location || "KONUM SEÇİLMEDİ");color:Theme.accent;font.pixelSize:10;font.letterSpacing:1}
        }
        Pill {label:"×";onClicked:panel.controller.openPanel=""}
    }
    Flow {
        Layout.fillWidth:true;spacing:6
        Repeater {
            model:[{id:"daily",name:"Günlük"},{id:"media",name:"Medya"},{id:"music",name:"YT Music"},{id:"video",name:"YouTube"},{id:"feeds",name:"RSS"},{id:"reddit",name:"Reddit"},{id:"accounts",name:"Hesaplar"},{id:"weather",name:"Hava / vakit"},{id:"finance",name:"Piyasalar"},{id:"system",name:"Sistem"},{id:"audio",name:"Ses"},{id:"display",name:"Ekran"},{id:"lid",name:"Kapak"},{id:"tablet",name:"Tablet"},{id:"tools",name:"Araçlar"},{id:"settings",name:"Ayarlar"}]
            Pill {required property var modelData;label:modelData.name;fill:panel.section===modelData.id ? "#46385d" : Theme.raised;onClicked:panel.change(modelData.id)}
        }
    }
    Text {Layout.fillWidth:true;text:panel.bridge.message;color:Theme.muted;font.pixelSize:11;textFormat:Text.PlainText;wrapMode:Text.WordWrap}
    KingdomTicker {Layout.fillWidth:true;bridge:panel.bridge;visible:["daily","feeds"].indexOf(panel.section)>=0}

    KingdomMedia {Layout.fillWidth:true;bridge:panel.bridge;visible:["daily","media","music"].indexOf(panel.section)>=0}
    RowLayout {
        visible:["music","video","radio"].indexOf(panel.section)>=0;Layout.fillWidth:true
        KingdomInput {id:search;Layout.fillWidth:true;placeholderText:panel.section==="radio" ? "Türk radyo istasyonu ara" : "Şarkı veya video ara";onAccepted:searchButton.clicked()}
        Pill {id:searchButton;label:"Ara";onClicked:if(search.text.trim()) panel.bridge.call(panel.section==="music" ? "search-music" : panel.section==="radio" ? "radio-search" : "search-video",search.text.trim())}
    }
    Flow {
        visible:panel.section==="radio";Layout.fillWidth:true;spacing:8
        Repeater {model:panel.bridge.state.radios || [];Pill {required property var modelData;label:modelData.name;onClicked:panel.bridge.call("play",{title:modelData.name,url:modelData.url})}}
    }
    ColumnLayout {
        visible:["music","video","radio"].indexOf(panel.section)>=0;Layout.fillWidth:true
        Repeater {
            model:panel.searchResults
            RowLayout {
                required property var modelData;Layout.fillWidth:true
                Text {Layout.fillWidth:true;text:modelData.title+"  "+(modelData.artist || "");color:Theme.pale;elide:Text.ElideRight;font.pixelSize:12;textFormat:Text.PlainText}
                Pill {label:"▶";onClicked:panel.bridge.call(panel.section==="video" ? "play-video" : "play",modelData)}
                Pill {label:"+ sıra";onClicked:panel.bridge.call("enqueue",modelData)}
                Pill {label:"Sonra";visible:panel.section==="video";onClicked:panel.bridge.call("later-add",modelData)}
            }
        }
    }
    ColumnLayout {
        visible:["media","music","video"].indexOf(panel.section)>=0;Layout.fillWidth:true
        Text {text:"OYNATMA SIRASI / SONRA İZLE";color:Theme.accent;font.pixelSize:10}
        RowLayout {Pill {label:"Önceki";onClicked:panel.bridge.call("mpv","playlist-prev")} Pill {label:"Duraklat / sürdür";onClicked:panel.bridge.call("mpv","pause")} Pill {label:"Sonraki";onClicked:panel.bridge.call("mpv","playlist-next")}}
        Repeater {model:panel.bridge.model("upcoming",(panel.bridge.state.upcoming || []).slice(0,3));Text {required property var modelData;Layout.fillWidth:true;text:"◇ "+modelData.title;color:Theme.pale;font.pixelSize:12;elide:Text.ElideRight;textFormat:Text.PlainText}}
        Text {text:"Sonra izle: "+panel.bridge.state.later.length+" içerik · "+Math.round(panel.bridge.state.later.reduce((sum,e)=>sum+(e.duration || 0),0)/60)+" dk (süresi bilinenler)";color:Theme.muted;font.pixelSize:11}
        Repeater {model:panel.bridge.state.later;RowLayout {required property var modelData;Layout.fillWidth:true;Text {Layout.fillWidth:true;text:modelData.title;color:Theme.pale;font.pixelSize:12;elide:Text.ElideRight;textFormat:Text.PlainText} Pill {label:"▶";onClicked:panel.bridge.call("play-video",modelData)} Pill {label:"×";onClicked:panel.bridge.call("later-remove",modelData.url)}}}
    }
    ColumnLayout {
        visible:["daily","pomodoro"].indexOf(panel.section)>=0;Layout.fillWidth:true
        RowLayout {
            Text {Layout.fillWidth:true;text:"POMODORO  ·  "+Math.floor((panel.bridge.state.pomodoro.remaining || 0)/60)+":"+String((panel.bridge.state.pomodoro.remaining || 0)%60).padStart(2,"0");color:Theme.accent;font.pixelSize:21;font.family:Theme.serif}
            Pill {label:"25 dk";onClicked:panel.bridge.call("pomodoro","work")}
            Pill {label:"5 dk mola";onClicked:panel.bridge.call("pomodoro","break")}
            Pill {label:panel.bridge.state.pomodoro.running ? "Duraklat" : "Sürdür";onClicked:panel.bridge.call("pomodoro",panel.bridge.state.pomodoro.running ? "pause" : "resume")}
        }
        RowLayout {Layout.fillWidth:true;KingdomInput {id:task;Layout.fillWidth:true;placeholderText:"Bugünün görevi"} Pill {label:"Ekle";onClicked:if(task.text.trim()){panel.bridge.call("task-add",task.text.trim());task.text="";}}}
        Repeater {model:panel.bridge.state.tasks;RowLayout {required property var modelData;Layout.fillWidth:true;Pill {label:modelData.done ? "✓" : "○";onClicked:if(modelData.id)panel.bridge.call("task-toggle",modelData.id)} Text {Layout.fillWidth:true;text:modelData.text;color:modelData.done ? Theme.dim : Theme.pale;font.pixelSize:13;wrapMode:Text.WordWrap;textFormat:Text.PlainText}}}
        Repeater {model:panel.bridge.state.goals;Text {required property var modelData;Layout.fillWidth:true;text:"HEDEF · "+(modelData.text || modelData);color:Theme.muted;font.pixelSize:12;wrapMode:Text.WordWrap;textFormat:Text.PlainText}}
        Text {text:panel.status("calendar");color:Theme.dim;font.pixelSize:10}
        Repeater {model:panel.bridge.model("calendar",panel.rows("calendar").slice(0,8));Text {required property var modelData;Layout.fillWidth:true;text:modelData.time+" · "+modelData.title;color:Theme.pale;font.pixelSize:12;wrapMode:Text.WordWrap;textFormat:Text.PlainText}}
    }
    ColumnLayout {
        visible:["daily","weather"].indexOf(panel.section)>=0;Layout.fillWidth:true
        Text {text:"HAVA · "+(panel.bridge.data("weather").current ? panel.bridge.data("weather").current.temperature_2m+" °C" : "—");color:Theme.pale;font.pixelSize:23;font.family:Theme.serif}
        Text {text:panel.status("weather")+"   /   AQI: "+(panel.bridge.data("aqi").current ? panel.bridge.data("aqi").current.european_aqi : "—");color:Theme.muted;font.pixelSize:11}
        RowLayout {
            Layout.fillWidth:true
            Repeater {
                model:panel.bridge.data("weather").daily ? panel.bridge.data("weather").daily.time : []
                ColumnLayout {required property int index;required property string modelData;Layout.fillWidth:true;Text {text:modelData.slice(5);color:Theme.accent;font.pixelSize:12} Text {text:panel.bridge.data("weather").daily.temperature_2m_min[index]+" / "+panel.bridge.data("weather").daily.temperature_2m_max[index]+"°";color:Theme.pale;font.pixelSize:12} Text {text:"Yağış %"+panel.bridge.data("weather").daily.precipitation_probability_max[index];color:Theme.muted;font.pixelSize:10}}
            }
        }
        KingdomSparkline {Layout.fillWidth:true;Layout.preferredHeight:45;values:panel.bridge.data("weather").daily ? panel.bridge.data("weather").daily.precipitation_probability_max : []}
        Text {Layout.fillWidth:true;text:panel.bridge.data("weather").daily ? "Gün doğumu "+panel.bridge.data("weather").daily.sunrise[0].slice(11)+" · batımı "+panel.bridge.data("weather").daily.sunset[0].slice(11)+" · Ay evresi ≈ "+(panel.bridge.data("today").moonPhase ?? "—") : "";color:Theme.muted;font.pixelSize:11;wrapMode:Text.WordWrap}
        Text {
            property var next: (panel.bridge.data("prayer").items || []).find(e=>e.timestamp>panel.bridge.state.now)
            text:next ? "Sıradaki vakit: "+next.name+" · "+Math.floor((next.timestamp-panel.bridge.state.now)/3600)+" sa "+Math.floor(((next.timestamp-panel.bridge.state.now)%3600)/60)+" dk" : panel.status("prayer")
            color:Theme.accent;font.pixelSize:15
        }
        Flow {Layout.fillWidth:true;spacing:8;Repeater {model:(panel.bridge.data("prayer").items || []).slice(0,6);Text {required property var modelData;text:modelData.name+" "+modelData.time;color:Theme.pale;font.pixelSize:12}}}
        Text {Layout.fillWidth:true;text:panel.bridge.data("prayer").source || "";color:Theme.dim;font.pixelSize:10;wrapMode:Text.WordWrap}
    }
    ColumnLayout {
        visible:["feeds","daily","reddit"].indexOf(panel.section)>=0;Layout.fillWidth:true
        Text {text:"KAYNAKLAR · "+panel.status("feeds");color:Theme.accent;font.pixelSize:11}
        Repeater {
            model:panel.bridge.model("sources",(panel.bridge.data("feeds").sources || []).filter(e=>panel.section!=="reddit" || e.kind==="reddit"))
            ColumnLayout {
                required property var modelData;Layout.fillWidth:true
                RowLayout {Layout.fillWidth:true;Text {Layout.fillWidth:true;text:modelData.name+" · "+(modelData.count===null ? "veri yok" : modelData.count+" yeni");color:Theme.pale;font.pixelSize:14;textFormat:Text.PlainText} Pill {label:"Okundu";onClicked:panel.bridge.call("mark-feed",modelData.id)}}
                Repeater {
                    model:modelData.items.slice(0,panel.section==="daily" ? 1 : 5)
                    RowLayout {required property var modelData;Layout.fillWidth:true;Text {Layout.fillWidth:true;text:modelData.title;color:Theme.muted;font.pixelSize:12;elide:Text.ElideRight;textFormat:Text.PlainText} Pill {label:"Aç";onClicked:panel.bridge.call("open-url",modelData.url)} Pill {label:"▶";visible:!!modelData.audio || modelData.url.indexOf("youtube")>=0;onClicked:panel.bridge.call(modelData.audio ? "play" : "play-video",{title:modelData.title,url:modelData.audio || modelData.url})}}
                }
            }
        }
    }
    ColumnLayout {
        visible:["accounts","reddit"].indexOf(panel.section)>=0;Layout.fillWidth:true
        Text {text:"Reddit: "+(panel.bridge.provider("reddit").status==="ready" ? panel.bridge.data("reddit").username+" · karma "+panel.bridge.data("reddit").karma+" · okunmamış "+panel.bridge.data("reddit").unread+(panel.bridge.data("reddit").capped ? "+" : "") : panel.status("reddit"));color:Theme.pale;font.pixelSize:12;Layout.fillWidth:true;wrapMode:Text.WordWrap}
        Text {text:"E-posta: "+(panel.bridge.provider("mail").status==="ready" ? panel.bridge.data("mail").unread+" okunmamış" : panel.status("mail"));color:Theme.pale;font.pixelSize:12;Layout.fillWidth:true;wrapMode:Text.WordWrap}
        Text {text:"GitHub: "+(panel.bridge.provider("github").status==="ready" ? panel.bridge.data("github").count+(panel.bridge.data("github").capped ? "+" : "")+" bildirim" : panel.status("github"));color:Theme.pale;font.pixelSize:12;Layout.fillWidth:true;wrapMode:Text.WordWrap}
        Repeater {model:panel.section==="reddit" ? panel.bridge.data("reddit").saved || [] : panel.rows("github");RowLayout {required property var modelData;Layout.fillWidth:true;Text {Layout.fillWidth:true;text:modelData.title;color:Theme.muted;elide:Text.ElideRight;font.pixelSize:12;textFormat:Text.PlainText} Pill {label:"Aç";onClicked:panel.bridge.call("open-url",modelData.url)}}}
        Text {text:"Twitch · "+panel.status("twitch");color:Theme.accent;font.pixelSize:12}
        Repeater {model:panel.rows("twitch");Pill {required property var modelData;Layout.fillWidth:true;label:modelData.name+" · "+modelData.title;onClicked:panel.bridge.call("open-url",modelData.url)}}
    }
    ColumnLayout {
        visible:panel.section==="finance";Layout.fillWidth:true
        Text {Layout.fillWidth:true;text:panel.bridge.data("finance").error || "";visible:!!text;color:Theme.muted;font.pixelSize:11}
        Text {text:panel.status("finance")+" / "+panel.status("stocks");color:Theme.muted;font.pixelSize:11;Layout.fillWidth:true;wrapMode:Text.WordWrap}
        Repeater {model:panel.bridge.model("markets",panel.rows("finance").concat(panel.rows("stocks")));ColumnLayout {required property var modelData;Layout.fillWidth:true;RowLayout {Layout.fillWidth:true;Text {Layout.fillWidth:true;text:modelData.symbol;color:Theme.pale;font.pixelSize:15;textFormat:Text.PlainText} Text {text:Number(modelData.value).toLocaleString()+" "+(modelData.currency || "TRY");color:Theme.accent;font.pixelSize:16}} KingdomSparkline {Layout.fillWidth:true;Layout.preferredHeight:42;values:modelData.history || []} Text {Layout.fillWidth:true;text:modelData.source+" · "+(modelData.date || (modelData.timestamp ? Qt.formatDateTime(new Date(modelData.timestamp*1000),"dd.MM HH:mm") : ""));color:Theme.dim;font.pixelSize:10;wrapMode:Text.WordWrap}}}
    }
    ColumnLayout {
        visible:panel.section==="system";Layout.fillWidth:true
        Text {text:"YOGA 7 · "+panel.status("hardware");color:Theme.accent;font.pixelSize:12}
        Repeater {model:panel.bridge.data("hardware").temperatures || [];Text {required property var modelData;text:modelData.name+" · "+modelData.value.toFixed(1)+" °C";color:Theme.pale;font.pixelSize:13}}
        Text {text:(panel.bridge.data("hardware").fans || []).length ? "Fan: "+panel.bridge.data("hardware").fans.map(e=>e.name+" "+e.value+" rpm").join(" · ") : "Fan hızı: donanım veri paylaşmıyor";color:Theme.muted;font.pixelSize:12}
        Repeater {model:panel.bridge.data("hardware").batteries || [];Text {required property var modelData;Layout.fillWidth:true;text:modelData.name+" · %"+modelData.percent+" · sağlık "+(modelData.health===null ? "veri yok" : "%"+modelData.health.toFixed(1))+" · tahmin "+(modelData.estimate===null ? "veri yok" : Math.round(modelData.estimate/60)+" dk");color:Theme.pale;font.pixelSize:13;wrapMode:Text.WordWrap}}
        Repeater {model:panel.bridge.data("hardware").disks || [];Text {required property var modelData;text:modelData.path+" · doluluk %"+modelData.percent.toFixed(1)+" · boş "+(modelData.free/1073741824).toFixed(1)+" GiB";color:modelData.percent>=90 ? "#ffb4ab" : Theme.pale;font.pixelSize:13}}
        Repeater {model:panel.bridge.model("network",Object.keys(panel.bridge.state.network));Text {required property string modelData;text:modelData+" · ↓ "+(panel.bridge.state.network[modelData].down/1024).toFixed(1)+" KiB/s · ↑ "+(panel.bridge.state.network[modelData].up/1024).toFixed(1)+" KiB/s";color:Theme.pale;font.pixelSize:13}}
        Text {text:"Bluetooth · "+panel.status("bluetooth");color:Theme.accent;font.pixelSize:12}
        Repeater {model:panel.rows("bluetooth");Text {required property var modelData;text:modelData.name+" · pil "+(modelData.battery===null ? "aygıt paylaşmıyor" : "%"+modelData.battery);color:Theme.pale;font.pixelSize:12}}
        Text {text:"BUGÜNKÜ UYGULAMA SÜRESİ";color:Theme.accent;font.pixelSize:11}
        Repeater {model:Object.entries(panel.bridge.state.usage[Qt.formatDateTime(new Date(),"yyyy-MM-dd")] || {}).sort((a,b)=>b[1]-a[1]).slice(0,10);Text {required property var modelData;text:modelData[0]+" · "+Math.round(modelData[1]/60)+" dk";color:Theme.muted;font.pixelSize:12}}
        Text {text:"AFAD · "+panel.status("earthquakes");color:Theme.accent;font.pixelSize:11}
        Repeater {model:panel.bridge.model("earthquakes",panel.rows("earthquakes").slice(0,5));Text {required property var modelData;Layout.fillWidth:true;text:modelData.magnitude+" · "+modelData.title+" · "+modelData.time;color:Theme.pale;font.pixelSize:12;wrapMode:Text.WordWrap;textFormat:Text.PlainText}}
    }
    ColumnLayout {
        visible:panel.section==="tablet";Layout.fillWidth:true
        Text {text:panel.bridge.state.tablet.available ? "Yoga anahtarı: "+(panel.bridge.state.tablet.tablet ? "TABLET" : "LAPTOP") : "Yoga anahtarı verisi bekleniyor";color:Theme.pale;font.pixelSize:20;font.family:Theme.serif}
        Text {text:panel.bridge.state.tablet.sensor && panel.bridge.state.tablet.sensor.available ? "Yön sensörü: "+panel.bridge.state.tablet.sensor.orientation : "Yön sensörü bulunamadı / erişilemedi";color:Theme.muted;font.pixelSize:12}
        Text {text:"Tercih: "+(panel.bridge.state.tablet.override===null || panel.bridge.state.tablet.override===undefined ? "Otomatik" : panel.bridge.state.tablet.override ? "Tablet" : "Laptop")+" · dönüş "+(panel.bridge.state.tablet.settings && panel.bridge.state.tablet.settings.rotation ? "açık" : "kapalı")+" · sanal klavye "+(panel.bridge.state.tablet.settings && panel.bridge.state.tablet.settings.keyboard ? "açık" : "kapalı");color:Theme.accent;font.pixelSize:12}
        RowLayout {Repeater {model:[{id:"auto",label:"Otomatik"},{id:"on",label:"Tablet"},{id:"off",label:"Laptop"}];Pill {required property var modelData;label:modelData.label;onClicked:panel.bridge.call("tablet",modelData.id)}}}
        RowLayout {Pill {label:"Sanal klavye";onClicked:panel.bridge.call("tablet","keyboard-toggle")} Pill {label:"Otomatik dönüş";onClicked:panel.bridge.call("tablet","rotation-toggle")}}
        Text {Layout.fillWidth:true;text:"Dahili klavye ve touchpad laptop modunda önceki davranışına döner. Harici mouse/klavye kullanılmaya devam eder.";color:Theme.muted;font.pixelSize:12;wrapMode:Text.WordWrap}
    }
    ColumnLayout {
        visible:panel.section==="notes";Layout.fillWidth:true
        QQC.TextArea {id:note;Layout.fillWidth:true;Layout.preferredHeight:300;color:Theme.pale;font.pixelSize:14;wrapMode:TextEdit.Wrap;selectByMouse:true;background:Rectangle {color:Theme.background;radius:12} placeholderText:"Hızlı not…"}
        Pill {label:"Notu kaydet";onClicked:panel.bridge.call("notes-save",note.text)}
    }
    ColumnLayout {
        visible:panel.section==="calculator";Layout.fillWidth:true
        KingdomInput {id:formula;Layout.fillWidth:true;placeholderText:"Ör. (125 + 75) * 1.20";onAccepted:panel.bridge.call("calculate",text)}
        Pill {label:"Hesapla";onClicked:panel.bridge.call("calculate",formula.text)}
        Text {text:panel.calculation;color:Theme.accent;font.pixelSize:30}
    }
    Flow {
        visible:panel.section==="emoji";Layout.fillWidth:true;spacing:7
        Repeater {model:["😀","🙂","😍","❤","💜","✨","🔥","🎵","📚","⚖","✓","✗","→","←","∞","§","¶","€","₺","α","β","γ","Δ","π","Ω","©","®","™","…","—","«","»"];Pill {required property string modelData;label:modelData;onClicked:panel.bridge.call("copy",modelData)}}
    }
    ColumnLayout {
        visible:panel.section==="clipboard";Layout.fillWidth:true
        Repeater {model:panel.clipboard;Pill {required property var modelData;Layout.fillWidth:true;label:modelData.text.slice(0,100);onClicked:panel.bridge.call("clipboard-copy",modelData.id)}}
    }
    // VIOLET_DEVICES_V2
    ColumnLayout {
        Layout.fillWidth:true
        visible:["audio","display","lid"].indexOf(panel.section)>=0
        Control {
            visible:panel.section==="audio";Layout.fillWidth:true
            label:"Ses seviyesi";value:panel.controller.volume
            onAdjusted:n=>panel.controller.setVolume(n)
        }
        Loader {
            id:violetDevicesLoader
            Layout.fillWidth:true
            active:["audio","display","lid"].indexOf(panel.section)>=0
            asynchronous:true
            source:Qt.resolvedUrl("VioletDevices.qml")
            onLoaded:item.section=Qt.binding(()=>panel.section)
        }
        Text {
            Layout.fillWidth:true;visible:violetDevicesLoader.status===Loader.Error
            text:"Ses / ekran / kapak bileşeni yüklenemedi. Mevcut bar çalışmaya devam ediyor."
            color:"#ffb4ab";font.pixelSize:12;wrapMode:Text.WordWrap
        }
    }
    Flow {
        visible:["tools","connectivity","power","commands"].indexOf(panel.section)>=0;Layout.fillWidth:true;spacing:8
        Repeater {model:panel.section==="commands" ? [] : [{id:"notes",name:"Hızlı not"},{id:"calculator",name:"Hesap makinesi"},{id:"clipboard",name:"Pano"},{id:"emoji",name:"Emoji / simge"},{id:"audio",name:"Ses çıkışı"},{id:"power",name:"Güç"},{id:"connectivity",name:"Bağlantılar"},{id:"radio",name:"Radyo"},{id:"commands",name:"Komutlar"}];Pill {required property var modelData;label:modelData.name;onClicked:panel.change(modelData.id)}}
        Pill {label:"Terminal";visible:panel.section==="tools";onClicked:panel.controller.command(["qtile","cmd-obj","-o","group","kingdom-scratch","-f","dropdown_toggle","-a","terminal"])}
        Pill {label:"LinguaMap";visible:panel.section==="tools";onClicked:panel.bridge.call("translation")}
        Pill {label:"Şimdi çalıyor overlay";visible:panel.section==="tools";onClicked:panel.controller.command(["kingdom-overlay"])}
        Pill {label:"Wi-Fi";visible:panel.section==="connectivity";onClicked:panel.bridge.call("connectivity","wifi")}
        Pill {label:"Bluetooth";visible:panel.section==="connectivity";onClicked:panel.bridge.call("connectivity","bluetooth")}
        Repeater {model:panel.section==="tools" ? [{id:"area",name:"Alan görüntüsü"},{id:"window",name:"Pencere görüntüsü"},{id:"screen",name:"Tüm ekran"}] : [];Pill {required property var modelData;label:modelData.name;onClicked:{panel.controller.openPanel="";panel.bridge.call("screenshot",modelData.id);}}}
        Repeater {model:panel.section==="power" ? [{id:"lock",name:"Kilitle"},{id:"suspend",name:"Uyut"},{id:"reboot",name:"Yeniden başlat"},{id:"off",name:"Kapat"}] : [];Pill {required property var modelData;label:panel.confirmPower===modelData.id ? "Onayla: "+modelData.name : modelData.name;onClicked:if(modelData.id==="lock" || panel.confirmPower===modelData.id)panel.bridge.call("power",modelData.id);else panel.confirmPower=modelData.id}}
        Repeater {model:panel.section==="commands" ? panel.bridge.state.commands : [];Pill {required property var modelData;label:modelData.name;onClicked:panel.bridge.call("saved-command",modelData.id)}}
    }
    ColumnLayout {
        visible:panel.section==="daily";Layout.fillWidth:true
        Text {text:"BUGÜN TARİHTE";color:Theme.accent;font.pixelSize:11}
        Text {Layout.fillWidth:true;text:panel.bridge.data("today").word ? JSON.stringify(panel.bridge.data("today").word) : "Günün kelimesi için kendi kelime listenizi ekleyin";color:Theme.muted;font.pixelSize:12;wrapMode:Text.WordWrap;textFormat:Text.PlainText}
        Repeater {model:panel.bridge.model("today",(panel.bridge.data("today").events || []).slice(0,3));Text {required property var modelData;Layout.fillWidth:true;text:modelData.year+" · "+modelData.text;color:Theme.pale;font.pixelSize:12;wrapMode:Text.WordWrap;textFormat:Text.PlainText}}
        Text {text:"CANLI SKOR · "+panel.status("sports");color:Theme.accent;font.pixelSize:11}
        Repeater {model:panel.rows("sports");Text {required property var modelData;Layout.fillWidth:true;text:modelData.title+" · "+JSON.stringify(modelData.score);color:Theme.pale;font.pixelSize:13;textFormat:Text.PlainText;wrapMode:Text.WordWrap}}
    }
    ColumnLayout {
        visible:panel.section==="settings";Layout.fillWidth:true
        RowLayout {Layout.fillWidth:true;KingdomInput {id:city;Layout.fillWidth:true;placeholderText:"Şehir / ilçe ara"} Pill {label:"Konum bul";onClicked:panel.bridge.call("geocode",city.text)}}
        Flow {Layout.fillWidth:true;spacing:6;Repeater {model:panel.cities;Pill {required property var modelData;label:modelData.name+" / "+(modelData.admin1 || modelData.country || "");onClicked:panel.bridge.call("location",{name:modelData.name,latitude:modelData.latitude,longitude:modelData.longitude,timezone:modelData.timezone || "Europe/Istanbul"})}}}
        Text {Layout.fillWidth:true;text:"Kaynak, görev ve uygulama tercihleri aşağıda düzenlenir. Hesap sırlarını secrets.env dosyasına yaz; bu alana yazma.";color:Theme.muted;font.pixelSize:12;wrapMode:Text.WordWrap}
        QQC.TextArea {id:settingsEditor;Layout.fillWidth:true;Layout.preferredHeight:340;color:Theme.pale;font.family:"monospace";font.pixelSize:11;selectByMouse:true;wrapMode:TextEdit.NoWrap;background:Rectangle {color:Theme.background;radius:12}}
        Pill {label:"Tercihleri kaydet";onClicked:{try{panel.bridge.call("settings-save",JSON.parse(settingsEditor.text));}catch(e){panel.bridge.message="JSON sözdizimini kontrol et";}}}
        Flow {Layout.fillWidth:true;spacing:6;Repeater {model:panel.bridge.model("provider-keys",Object.keys(panel.bridge.state.providers));Pill {required property string modelData;label:modelData+" · "+panel.bridge.provider(modelData).status;onClicked:panel.bridge.call("refresh",modelData)}}}
    }
}
