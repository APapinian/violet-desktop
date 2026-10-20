import QtQuick
import QtQuick.Layouts
ColumnLayout {
    id:dashboard
    required property var controller
    property string tab:controller.modernTab
    property var metrics:controller.modern.state
    spacing:18
    RowLayout {
        Layout.fillWidth:true
        Text {text:"VIOLET";color:Theme.accent;font.family:Theme.serif;font.pixelSize:22;font.letterSpacing:3}
        Item {Layout.fillWidth:true}
        Repeater {
            model:[{id:"dashboard",label:"Günlük"},{id:"media",label:"Medya"},{id:"system",label:"Sistem"},{id:"weather",label:"Hava"},{id:"buds",label:"Buds"}]
            Pill {required property var modelData;label:modelData.label;fill:dashboard.tab===modelData.id ? "#53406d" : Theme.raised;onClicked:dashboard.controller.modernTab=modelData.id}
        }
        Pill {label:"×";onClicked:dashboard.controller.openPanel=""}
    }
    Loader {
        Layout.fillWidth:true
        sourceComponent:dashboard.tab==="media" ? mediaPage : dashboard.tab==="buds" ? budsPage : dashboard.tab==="weather" ? weatherPage : dashboard.tab==="system" ? systemPage : dailyPage
    }
    Component {id:budsPage;BudsPanel {controller:dashboard.controller}}
    Component {id:mediaPage;RecordPlayer {controller:dashboard.controller}}
    Component {id:dailyPage;DailyOverview {controller:dashboard.controller}}
    Component {
        id:systemPage
        ColumnLayout {
            spacing:18
            RowLayout {MetricRing {value:dashboard.metrics.cpu;label:"CPU"} MetricRing {value:dashboard.metrics.memory;label:"Bellek"} MetricRing {value:dashboard.metrics.disk;label:"Disk"}}
            Text {text:"Pil: "+dashboard.controller.value(dashboard.controller.state.battery);color:Theme.pale;font.pixelSize:22}
            Text {text:"Çalışma süresi: "+Math.floor(dashboard.metrics.uptime/3600)+" saat";color:Theme.muted;font.pixelSize:13}
            Text {Layout.fillWidth:true;text:dashboard.controller.state.wifi || "Bağlantı bekleniyor";color:Theme.pale;font.pixelSize:13;textFormat:Text.PlainText}
            RowLayout {Pill {label:"Donanım ayrıntıları";onClicked:{dashboard.controller.featureSection="system";dashboard.controller.openPanel="features";}} Pill {label:"Bluetooth";onClicked:dashboard.controller.modernTab="buds"} Pill {label:"Tablet";onClicked:{dashboard.controller.featureSection="tablet";dashboard.controller.openPanel="features";}}}
        }
    }
    Component {
        id:weatherPage
        ColumnLayout {
            property var weather:dashboard.controller.features.data("weather")
            spacing:18
            Text {text:dashboard.controller.features.state.location || "Şehir seçilmedi";color:Theme.pale;font.family:Theme.serif;font.pixelSize:28}
            Text {text:parent.weather.current ? parent.weather.current.temperature_2m+"°" : "—°";color:Theme.accent;font.pixelSize:72}
            Text {text:dashboard.controller.features.provider("weather").error || "Open-Meteo";color:Theme.muted;font.pixelSize:12}
            RowLayout {Pill {label:"Tahmin ve namaz vakitleri";onClicked:{dashboard.controller.featureSection="weather";dashboard.controller.openPanel="features";}} Pill {label:"Şehir seç";onClicked:{dashboard.controller.featureSection="settings";dashboard.controller.openPanel="features";}}}
        }
    }
}
