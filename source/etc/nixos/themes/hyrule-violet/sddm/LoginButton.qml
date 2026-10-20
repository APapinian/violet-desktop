import QtQuick
import QtQuick.Controls.Basic as C
C.Button {
    id:button
    property bool prominent:false
    implicitHeight:46
    hoverEnabled:true
    font.pixelSize:13
    font.family:"sans-serif"
    contentItem:Text {
        text:button.text; textFormat:Text.PlainText
        color:button.prominent ? "#251a42" : "#ece4f8"
        font:button.font; horizontalAlignment:Text.AlignHCenter; verticalAlignment:Text.AlignVCenter
        opacity:button.enabled ? 1 : .45
    }
    background:Rectangle {
        radius:12
        color:button.prominent ? (button.down ? "#aaa1ba" : button.hovered ? "#ece4f8" : "#c5b4ff") : (button.hovered || button.activeFocus ? "#463c57" : "#251f32")
        border.width:button.activeFocus ? 2 : 1
        border.color:button.activeFocus ? "#c5b4ff" : "#463c57"
        Behavior on color {ColorAnimation {duration:140}}
    }
}
