import QtQuick
import Quickshell
import QtQuick.Layouts
ColumnLayout {
    id: player
    required property var controller
    property var bridge:controller.features
    property var current:(bridge.data("media").players || []).find(p=>p.player===controller.mediaPlayer) || bridge.data("media").current || ({})
    property bool playing:current.status==="Playing"
    property real position:Math.min(current.length || 0,(current.position || 0)+(playing ? Math.max(0,bridge.state.now-(bridge.provider("media").updated || bridge.state.now)) : 0))
    function action(command,extra) {if(current.player) controller.modern.call("player",Object.assign({player:current.player,command:command},extra || {}));}
    function time(seconds) {const n=Math.max(0,Math.floor(seconds || 0));return Math.floor(n/60)+":"+String(n%60).padStart(2,"0");}
    spacing:14
    RowLayout {
        Layout.fillWidth:true
        Text {Layout.fillWidth:true;text:"VIOLET / MELODİLER";color:Theme.accent;font.pixelSize:10;font.letterSpacing:2}
        Pill {label:"Ara";onClicked:{player.controller.featureSection="music";player.controller.openPanel="features";}}
        Pill {label:"Dosya";onClicked:{player.controller.openPanel="";player.controller.command(["violetctl","pick-music"]);}}
    }
    Item {
        Layout.alignment:Qt.AlignHCenter;Layout.preferredWidth:Math.min(player.width,340);Layout.preferredHeight:Math.min(player.width,340)
        Rectangle {anchors.fill:parent;anchors.margins:8;radius:width/2;color:"#101016";border.color:"#6e5b93";border.width:2}
        Item {
            id:vinyl;anchors.fill:parent;anchors.margins:12
            NumberAnimation on rotation {from:0;to:360;duration:20000;loops:Animation.Infinite;running:true;paused:!player.playing || Theme.reducedMotion}
            Canvas {
                anchors.fill:parent
                onPaint:{const c=getContext("2d");c.reset();const r=width/2;for(let x=43;x<r-6;x+=4){c.beginPath();c.arc(r,r,x,0,Math.PI*2);c.strokeStyle=x%3 ? "#25212c" : "#342c3f";c.lineWidth=1;c.stroke();}c.beginPath();c.arc(r,r,r-8,3.3,4.6);c.strokeStyle="#5e506d";c.lineWidth=2;c.stroke();}
            }
            Canvas {
                id:album;anchors.centerIn:parent;width:parent.width*.40;height:width
                property string art:player.current.art || ""
                onArtChanged:{if(art) loadImage(art);requestPaint();}
                Component.onCompleted:if(art)loadImage(art)
                onImageLoaded:requestPaint()
                onPaint:{const c=getContext("2d");c.reset();c.save();c.beginPath();c.arc(width/2,height/2,width/2,0,Math.PI*2);c.clip();c.fillStyle="#49375e";c.fillRect(0,0,width,height);if(art && isImageLoaded(art))c.drawImage(art,0,0,width,height);c.restore();}
                Text {anchors.centerIn:parent;text:"✦";font.pixelSize:42;color:Theme.accent;visible:!album.art}
            }
            Rectangle {anchors.centerIn:parent;width:9;height:9;radius:5;color:Theme.background;border.color:Theme.accent}
        }
        Item {
            id:arm
            width:parent.width*.32;height:parent.height*.76
            x:parent.width*.61;y:parent.height*.07
            rotation:player.playing ? 12 : -12;transformOrigin:Item.TopRight
            Behavior on rotation {NumberAnimation {duration:Theme.duration(600);easing.type:Easing.InOutCubic}}
            Canvas {
                anchors.fill:parent
                onPaint:{const c=getContext("2d");c.reset();c.beginPath();c.moveTo(width-13,18);c.lineTo(width-25,height*.7);c.lineTo(width*.38,height-20);c.strokeStyle="#c5b4ff";c.lineWidth=4;c.lineCap="round";c.stroke();c.beginPath();c.arc(width-13,18,8,0,Math.PI*2);c.fillStyle="#584172";c.fill();c.strokeStyle="#ddceff";c.lineWidth=2;c.stroke();c.fillStyle="#ddceff";c.save();c.translate(width*.38,height-20);c.rotate(.4);c.fillRect(-6,0,12,23);c.restore();}
            }
        }
    }
    Text {Layout.fillWidth:true;text:player.current.title || "Henüz bir şey çalmıyor";font.family:Theme.serif;font.pixelSize:24;color:Theme.pale;elide:Text.ElideRight;textFormat:Text.PlainText}
    Text {Layout.fillWidth:true;text:player.current.artist || "YouTube Music · mpv · MPRIS";color:Theme.muted;font.pixelSize:12;elide:Text.ElideRight;textFormat:Text.PlainText}
    Control {Layout.fillWidth:true;label:player.time(player.position)+" / "+player.time(player.current.length);suffix:"%";value:player.current.length ? player.position/player.current.length*100 : 0;onAdjusted:n=>{if(player.current.length)player.action("seek",{seconds:n*player.current.length/100});}}
    RowLayout {
        Layout.alignment:Qt.AlignHCenter;spacing:9
        Pill {label:"⇄";onClicked:player.action("shuffle")}
        Pill {label:"◀";onClicked:player.action("previous")}
        Pill {label:player.playing ? "Ⅱ" : "▶";fill:"#584172";onClicked:player.action("play-pause")}
        Pill {label:"▶▶";onClicked:player.action("next")}
        Pill {label:"↻";onClicked:player.action("loop",{mode:"Track"})}
        Pill {label:"↻ ×";onClicked:player.action("loop",{mode:"None"})}
    }
    Text {Layout.fillWidth:true;text:player.bridge.state.lyrics.line || "";color:Theme.accent;font.pixelSize:14;wrapMode:Text.WordWrap;textFormat:Text.PlainText}
    Flow {Layout.fillWidth:true;spacing:6;Repeater {model:player.bridge.data("media").players || [];Pill {required property var modelData;label:modelData.player;fill:player.current.player===modelData.player ? "#53406d" : Theme.raised;onClicked:player.controller.mediaPlayer=modelData.player}}}
    Text {Layout.fillWidth:true;text:player.controller.modern.message;color:Theme.muted;font.pixelSize:11;wrapMode:Text.WordWrap;textFormat:Text.PlainText}
}
