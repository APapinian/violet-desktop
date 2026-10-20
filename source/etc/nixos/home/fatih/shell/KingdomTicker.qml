import QtQuick
RuneFrame {
    id:ticker
    required property var bridge
    property int index:0
    property var items:bridge.state.headlines || []
    property var current:items.length ? items[index % items.length] : null
    implicitHeight:42;ornament:false;clip:true
    Item {
        anchors.fill:parent;anchors.margins:10;clip:true
        Text {
            id:title
            text:ticker.current ? ticker.current.title : "Haber kaynağı eklenmedi"
            font.family:Theme.sans;font.pixelSize:12;color:Theme.pale;textFormat:Text.PlainText
            y:(parent.height-height)/2
            x:0
            SequentialAnimation on x {
                running:ticker.visible && !Theme.reducedMotion && title.implicitWidth>ticker.width-20
                loops:Animation.Infinite
                PauseAnimation {duration:1500}
                NumberAnimation {from:0;to:Math.min(0,ticker.width-30-title.implicitWidth);duration:Math.min(45000,Math.max(3000,title.implicitWidth*30))}
                PauseAnimation {duration:1500}
                NumberAnimation {to:0;duration:0}
            }
        }
    }
    Timer {interval:15000;repeat:true;running:ticker.visible && ticker.items.length>1;onTriggered:ticker.index++}
    MouseArea {anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:if(ticker.current) ticker.bridge.call("open-url",ticker.current.url)}
}
