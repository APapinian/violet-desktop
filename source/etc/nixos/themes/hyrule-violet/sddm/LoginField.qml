import QtQuick
import QtQuick.Controls.Basic as C
C.TextField {
    id:field
    implicitHeight:50
    color:"#ece4f8";placeholderTextColor:"#aaa1ba"
    font.pixelSize:15;selectionColor:"#c5b4ff";selectedTextColor:"#251a42"
    leftPadding:16;rightPadding:16
    background:Rectangle {
        color:"#100f18";radius:12
        border.width:field.activeFocus ? 2 : 1
        border.color:field.activeFocus ? "#c5b4ff" : "#463c57"
        Behavior on border.color {ColorAnimation {duration:160}}
    }
}
