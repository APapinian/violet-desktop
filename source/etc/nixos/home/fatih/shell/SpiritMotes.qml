import QtQuick
Item {
    id: spirits
    property bool active: false
    property int density: 18
    Repeater {
        model: spirits.density
        Item {
            id: mote
            required property int index
            property real travel: 0
            x: spirits.width * ((index * .61803398875) % 1)
            y: spirits.height * (1.05 - travel * 1.2)
            opacity: Math.sin(travel * Math.PI) * .65
            Rectangle {
                width: mote.index % 3 === 0 ? 4 : 2; height: width
                rotation: 45; radius: mote.index % 3 === 0 ? 0 : 2
                color: mote.index % 2 === 0 ? Theme.accent : Theme.pale
                x: Math.sin(mote.travel * 6.28 + mote.index) * 20
            }
            NumberAnimation on travel {
                running: spirits.active && Theme.ambientEnabled && !Theme.reducedMotion
                loops: Animation.Infinite; from: 0; to: 1
                duration: 2800 + mote.index * 137
            }
        }
    }
}
