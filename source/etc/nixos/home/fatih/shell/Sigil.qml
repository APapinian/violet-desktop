import QtQuick
Item {
    id: sigil
    property string name: "triforce"
    implicitWidth: 24
    implicitHeight: 24
    Image {
        objectName: "raster"
        anchors.fill: parent
        source: Qt.resolvedUrl("assets/icons/" + sigil.name + ".svg")
        sourceSize: Qt.size(128, 128)
        fillMode: Image.PreserveAspectFit
        smooth: true
        mipmap: true
    }
}
