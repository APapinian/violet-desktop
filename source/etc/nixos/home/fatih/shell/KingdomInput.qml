import QtQuick
import QtQuick.Controls
TextField {
    id: field
    font.family: Theme.sans
    font.pixelSize: 13
    color: Theme.pale
    placeholderTextColor: Theme.dim
    selectByMouse: true
    implicitHeight: 42
    background: Rectangle { color:Theme.background;radius:10;border.color:field.activeFocus ? Theme.accent : Theme.border }
    leftPadding: 13; rightPadding: 13
}
