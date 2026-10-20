import QtQuick
Canvas {
    id: chart
    property var values: []
    property color lineColor: Theme.accent
    onValuesChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        const ctx=getContext("2d");ctx.clearRect(0,0,width,height);
        if(values.length<2) return;
        const lo=Math.min(...values), hi=Math.max(...values), span=hi-lo || 1;
        ctx.strokeStyle=lineColor;ctx.lineWidth=2;ctx.beginPath();
        values.forEach((v,i)=>{const x=i*width/(values.length-1),y=height-4-(v-lo)*(height-8)/span;if(i)ctx.lineTo(x,y);else ctx.moveTo(x,y);});
        ctx.stroke();
    }
}
