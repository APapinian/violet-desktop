import QtQuick
import QtQuick.Controls.Basic as C
import QtQuick.Layouts

Rectangle {
    id:root
    objectName:"loginRoot"
    width:1920;height:1200;color:"#100f18"
    property bool entered:false
    property bool busy:false
    property string failure:""
    property string powerAction:""
    property string clockText:Qt.formatDateTime(new Date(),"HH:mm")
    readonly property string titleFamily:titleFont.status===FontLoader.Ready ? titleFont.name : "serif"
    FontLoader {id:titleFont;source:Qt.resolvedUrl("assets/DejaVuSerif.ttf")}
    function login() {
        if (busy || !username.text.trim() || sessions.currentIndex<0) return;
        failure="";busy=true;
        sddm.login(username.text.trim(),password.text,sessions.currentIndex);
    }
    function power() {
        if (powerAction==="reboot" && sddm.canReboot) sddm.reboot();
        else if (powerAction==="off" && sddm.canPowerOff) sddm.powerOff();
        powerAction="";
    }
    Component.onCompleted:{entered=true;password.forceActiveFocus();}
    Connections {
        target:sddm
        function onLoginFailed() {root.busy=false;root.failure="Giriş başarısız. Kullanıcı adını ve parolanı kontrol et.";password.text="";password.forceActiveFocus();}
        function onLoginSucceeded() {root.failure="";password.text="";}
    }
    Timer {interval:1000;running:true;repeat:true;onTriggered:root.clockText=Qt.formatDateTime(new Date(),"HH:mm")}
    Image {
        anchors.fill:parent;source:Qt.resolvedUrl("assets/background.png")
        sourceSize.width:1920;sourceSize.height:1200
        fillMode:Image.PreserveAspectCrop;asynchronous:true
    }
    Rectangle {
        anchors.fill:parent
        gradient:Gradient {
            orientation:Gradient.Horizontal
            GradientStop {position:0;color:"#f0100f18"}
            GradientStop {position:.52;color:"#77100f18"}
            GradientStop {position:1;color:"#55100f18"}
        }
    }
    Rectangle {anchors.bottom:parent.bottom;width:parent.width;height:190;gradient:Gradient {GradientStop {position:0;color:"transparent"} GradientStop {position:1;color:"#dd100f18"}}}
    Column {
        anchors.top:parent.top;anchors.right:parent.right;anchors.margins:Math.max(22,root.width*.04)
        spacing:6
        Text {anchors.right:parent.right;text:root.clockText;font.family:root.titleFamily;font.pixelSize:Math.min(66,root.width/14);color:"#ece4f8"}
        Text {anchors.right:parent.right;text:Qt.formatDateTime(new Date(),"dd.MM.yyyy");font.pixelSize:12;font.letterSpacing:2;color:"#c5b4ff"}
    }
    Flickable {
        id:viewport;objectName:"loginViewport"
        x:root.width>850 ? Math.max(32,root.width*.075) : 20
        y:Math.min(110,root.height*.14)
        width:Math.min(460,root.width-40);height:Math.max(160,root.height-y-82)
        contentWidth:width;contentHeight:form.height+30
        clip:true;boundsBehavior:Flickable.StopAtBounds
        C.ScrollBar.vertical:C.ScrollBar {policy:C.ScrollBar.AsNeeded}
        ColumnLayout {
            id:form;objectName:"loginForm"
            width:viewport.width;spacing:19
            opacity:root.entered ? 1 : 0
            transform:Translate {y:root.entered ? 0 : 20;Behavior on y {NumberAnimation {duration:650;easing.type:Easing.OutCubic}}}
            Behavior on opacity {NumberAnimation {duration:450}}
            Item {
                Layout.preferredWidth:100;Layout.preferredHeight:100
                Canvas {
                    anchors.fill:parent
                    onPaint:{
                        const c=getContext("2d");c.clearRect(0,0,width,height);c.strokeStyle="#c5b4ff";c.lineWidth=1;
                        c.beginPath();c.arc(50,50,46,0,Math.PI*2);c.stroke();c.fillStyle="#c5b4ff";
                        for(const p of [[50,23,64,47,36,47],[35,49,49,73,21,73],[65,49,79,73,51,73]]){c.beginPath();c.moveTo(p[0],p[1]);c.lineTo(p[2],p[3]);c.lineTo(p[4],p[5]);c.closePath();c.fill();}
                    }
                }
                Rectangle {x:48;y:0;width:4;height:4;radius:2;color:"#ece4f8"}
            }
            Text {text:"H Y R U L E  /  V I O L E T";color:"#c5b4ff";font.pixelSize:10;font.letterSpacing:2}
            Text {
                Layout.fillWidth:true;text:"Krallığa hoş geldin,\nFatih."
                color:"#ece4f8";font.family:root.titleFamily;font.pixelSize:Math.min(45,viewport.width/9)
                lineHeight:1.2;wrapMode:Text.WordWrap
            }
            Text {Layout.fillWidth:true;text:"Yolculuğun kaldığı yerden devam ediyor.";color:"#aaa1ba";font.pixelSize:13;wrapMode:Text.WordWrap}
            Rectangle {Layout.fillWidth:true;height:1;color:"#463c57";Layout.topMargin:5;Layout.bottomMargin:3}
            Text {text:"KULLANICI";color:"#aaa1ba";font.pixelSize:10;font.letterSpacing:2}
            LoginField {
                id:username;objectName:"username";Layout.fillWidth:true
                text:(userModel && userModel.lastUser) || "fatih";placeholderText:"Kullanıcı adı"
                enabled:!root.busy;onAccepted:password.forceActiveFocus()
                KeyNavigation.tab:password
            }
            Text {text:"PAROLA";color:"#aaa1ba";font.pixelSize:10;font.letterSpacing:2}
            LoginField {
                id:password;objectName:"password";Layout.fillWidth:true
                placeholderText:"Krallığın anahtarı";enabled:!root.busy
                echoMode:C.TextField.Password
                inputMethodHints:Qt.ImhSensitiveData | Qt.ImhNoPredictiveText
                onAccepted:root.login();KeyNavigation.tab:sessions
            }
            Text {
                Layout.fillWidth:true;visible:keyboard && keyboard.capsLock
                text:"Caps Lock açık";color:"#c5b4ff";font.pixelSize:12
            }
            Text {text:"OTURUM";color:"#aaa1ba";font.pixelSize:10;font.letterSpacing:2}
            C.ComboBox {
                id:sessions;objectName:"sessions";Layout.fillWidth:true
                model:sessionModel;textRole:"name";enabled:!root.busy;implicitHeight:48
                currentIndex:count>0 ? Math.max(0,Math.min(count-1,sessionModel.lastIndex)) : -1
                font.pixelSize:13
                contentItem:Text {leftPadding:14;rightPadding:28;text:sessions.displayText;color:"#ece4f8";verticalAlignment:Text.AlignVCenter;elide:Text.ElideRight}
                background:Rectangle {color:"#17151f";radius:12;border.color:sessions.activeFocus ? "#c5b4ff" : "#463c57"}
                delegate:C.ItemDelegate {
                    required property string name
                    required property int index
                    width:sessions.width;text:name
                    contentItem:Text {text:parent.text;color:"#ece4f8";font.pixelSize:13;elide:Text.ElideRight;verticalAlignment:Text.AlignVCenter}
                    background:Rectangle {color:parent.highlighted ? "#463c57" : "#17151f"}
                    highlighted:sessions.highlightedIndex===index
                }
                popup:C.Popup {
                    y:sessions.height+5;width:sessions.width;padding:5
                    implicitHeight:Math.min(260,contentItem.implicitHeight+10)
                    contentItem:ListView {clip:true;implicitHeight:contentHeight;model:sessions.popup.visible ? sessions.delegateModel : null;currentIndex:sessions.highlightedIndex;C.ScrollIndicator.vertical:C.ScrollIndicator {}}
                    background:Rectangle {color:"#17151f";radius:12;border.color:"#463c57"}
                }
            }
            Text {Layout.fillWidth:true;visible:!!root.failure;text:root.failure;color:"#c5b4ff";wrapMode:Text.WordWrap;font.pixelSize:12;textFormat:Text.PlainText}
            Text {visible:sessions.count===0;text:"Oturum bulunamadı; sistem yapılandırmasını kontrol et.";color:"#c5b4ff";font.pixelSize:12;wrapMode:Text.WordWrap;Layout.fillWidth:true}
            LoginButton {objectName:"loginButton";Layout.fillWidth:true;text:root.busy ? "Kapı açılıyor…" : "Krallığa gir   →";prominent:true;enabled:!root.busy && sessions.count>0 && !!username.text.trim();onClicked:root.login()}
            RowLayout {
                Layout.fillWidth:true;spacing:8
                LoginButton {Layout.fillWidth:true;text:"Uyku";visible:sddm && sddm.canSuspend;enabled:!root.busy;onClicked:sddm.suspend()}
                LoginButton {Layout.fillWidth:true;text:"Yeniden başlat";visible:sddm && sddm.canReboot;enabled:!root.busy;onClicked:root.powerAction="reboot"}
                LoginButton {Layout.fillWidth:true;text:"Kapat";visible:sddm && sddm.canPowerOff;enabled:!root.busy;onClicked:root.powerAction="off"}
            }
        }
    }
    Row {
        anchors.bottom:parent.bottom;anchors.left:parent.left;anchors.margins:28;spacing:12
        Rectangle {width:28;height:1;color:"#c5b4ff";anchors.verticalCenter:parent.verticalCenter}
        Text {text:"CESARET  ·  BİLGELİK  ·  GÜÇ";font.pixelSize:9;font.letterSpacing:2;color:"#aaa1ba"}
    }
    C.Popup {
        id:confirm;anchors.centerIn:parent;width:Math.min(380,root.width-40)
        visible:!!root.powerAction;modal:true;focus:true;closePolicy:C.Popup.CloseOnEscape | C.Popup.CloseOnPressOutside
        onClosed:root.powerAction=""
        background:Rectangle {color:"#17151f";radius:18;border.color:"#463c57"}
        contentItem:ColumnLayout {
            spacing:18
            Text {Layout.fillWidth:true;text:root.powerAction==="reboot" ? "Yeniden başlatılsın mı?" : "Bilgisayar kapatılsın mı?";wrapMode:Text.WordWrap;color:"#ece4f8";font.family:root.titleFamily;font.pixelSize:21}
            RowLayout {LoginButton {text:"Vazgeç";onClicked:root.powerAction=""} LoginButton {text:"Onayla";prominent:true;onClicked:root.power()}}
        }
    }
}
