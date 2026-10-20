import QtQuick
import QtQuick.Layouts
ColumnLayout {
    id: calendar
    property date today: new Date()
    property int year: today.getFullYear()
    property int month: today.getMonth()
    property int first: (new Date(year,month,1).getDay()+6)%7
    property int days: new Date(year,month+1,0).getDate()
    property var months: ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
    spacing: 5
    Timer { interval:60000;running:true;repeat:true;onTriggered:calendar.today=new Date() }
    RowLayout {
        Layout.fillWidth: true
        Pill {label:"‹";implicitHeight:30;horizontalPadding:11;onClicked:{if(calendar.month===0){calendar.month=11;calendar.year--;}else calendar.month--;}}
        Text {Layout.fillWidth:true;text:calendar.months[calendar.month]+" "+calendar.year;color:Theme.pale;font.pixelSize:13;horizontalAlignment:Text.AlignHCenter}
        Pill {label:"›";implicitHeight:30;horizontalPadding:11;onClicked:{if(calendar.month===11){calendar.month=0;calendar.year++;}else calendar.month++;}}
    }
    GridLayout {
        Layout.fillWidth:true; columns:7; rowSpacing:4; columnSpacing:4
        Repeater { model:["Pt","Sa","Ça","Pe","Cu","Ct","Pz"];Text {required property string modelData;Layout.fillWidth:true;Layout.preferredHeight:22;text:modelData;color:Theme.dim;font.pixelSize:10;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter} }
        Repeater {
            model:42
            Rectangle {
                required property int index
                property int day:index-calendar.first+1
                property bool valid:day>=1 && day<=calendar.days
                property bool current:valid && day===calendar.today.getDate() && calendar.month===calendar.today.getMonth() && calendar.year===calendar.today.getFullYear()
                Layout.fillWidth:true;implicitHeight:28;radius:10
                color:current ? Theme.accent : "transparent"
                Text {anchors.centerIn:parent;text:parent.valid ? parent.day : "";color:parent.current ? Theme.ink : Theme.pale;font.pixelSize:12}
            }
        }
    }
}
