import QtQuick
Item {
    id: ripple
    property real cx: width / 2
    property real cy: height / 2
    property real progress: 1
    clip: true
    function burst(x, y) {
        if (Theme.reducedMotion) return;
        cx = x; cy = y; pulse.restart();
    }
    Rectangle {
        width: 12 + ripple.progress * 110; height: width; radius: width / 2
        x: ripple.cx - width / 2; y: ripple.cy - height / 2
        color: "transparent"; border.color: Theme.accent; border.width: 1
        opacity: (1 - ripple.progress) * .55
    }
    NumberAnimation { id: pulse; target: ripple; property: "progress"; from: 0; to: 1; duration: Theme.duration(520); easing.type: Easing.OutCubic }
}
