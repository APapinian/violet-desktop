import QtQuick
import QtQuick.Layouts
ColumnLayout {
    id: calendar
    property date today: new Date()
    property int year: today.getFullYear()
    property int month: today.getMonth()
    property int start: (new Date(year,month,1).getDay()+6)%7
    property int days: new Date(year,month+1,0).getDate()
    property var months:['Ocak','Şubat','Mart','Nisan','Mayıs','Haziran','Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık']
    spacing:16
    Timer { interval:60000; running:true; repeat:true; onTriggered:calendar.today=new Date() }
    Text { text:Qt.formatDateTime(calendar.today,'HH:mm'); color:'#d3c3ff'; font.family:'Rubik'; font.pixelSize:58 }
    RowLayout {
        Layout.fillWidth:true
        Pill { label:'‹'; onClicked:{ if(calendar.month===0){calendar.month=11;calendar.year--;}else calendar.month--; } }
        Text { Layout.fillWidth:true; text:calendar.months[calendar.month]+' '+calendar.year; color:'#ece4f8'; font.family:'Rubik'; font.pixelSize:16; horizontalAlignment:Text.AlignHCenter }
        Pill { label:'›'; onClicked:{ if(calendar.month===11){calendar.month=0;calendar.year++;}else calendar.month++; } }
    }
    GridLayout {
        Layout.fillWidth:true; columns:7; rowSpacing:4; columnSpacing:4
        Repeater {
            model:['Pt','Sa','Ça','Pe','Cu','Ct','Pz']
            Text { required property string modelData; Layout.fillWidth:true; text:modelData; color:'#a69ab6'; font.family:'Rubik'; font.pixelSize:11; horizontalAlignment:Text.AlignHCenter }
        }
        Repeater {
            model:42
            Rectangle {
                required property int index
                property int day:index-calendar.start+1
                property bool valid:day>0 && day<=calendar.days
                property bool current:valid && day===calendar.today.getDate() && calendar.month===calendar.today.getMonth() && calendar.year===calendar.today.getFullYear()
                Layout.fillWidth:true; implicitHeight:36; radius:12
                color:current ? '#c5b4ff' : valid ? '#262331' : 'transparent'
                Text { anchors.centerIn:parent; text:parent.valid ? parent.day : ''; color:parent.current ? '#251a42' : '#ece4f8'; font.family:'Rubik'; font.pixelSize:12 }
            }
        }
    }
    Pill { label:'Bugün'; onClicked:{calendar.year=calendar.today.getFullYear();calendar.month=calendar.today.getMonth();} }
}
