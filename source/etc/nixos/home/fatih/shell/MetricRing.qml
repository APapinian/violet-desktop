import QtQuick
Item {
    id:ring
    property real value:0
    property string label:""
    implicitWidth:96;implicitHeight:112
    Canvas {
        id:canvas;anchors.top:parent.top;width:parent.width;height:width
        Connections {target:ring;function onValueChanged(){canvas.requestPaint();}}
        onPaint:{const c=getContext("2d");c.reset();const r=width/2-8;c.lineWidth=5;c.lineCap="round";c.beginPath();c.arc(width/2,height/2,r,-Math.PI/2,Math.PI*1.5);c.strokeStyle="#3a304b";c.stroke();c.beginPath();c.arc(width/2,height/2,r,-Math.PI/2,-Math.PI/2+Math.PI*2*Math.max(0,Math.min(100,ring.value))/100);c.strokeStyle="#c5b4ff";c.stroke();}
        Text {anchors.centerIn:parent;text:Math.round(ring.value)+"%";color:Theme.pale;font.pixelSize:17}
    }
    Text {anchors.bottom:parent.bottom;anchors.horizontalCenter:parent.horizontalCenter;text:ring.label;color:Theme.muted;font.pixelSize:10}
}
