#!/usr/bin/env python3
"""Opaque painted card: no root stylesheet/translucency or early focus dismissal."""
import json, os, subprocess, sys
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QImageReader, QPixmap, QPainter, QColor, QPainterPath
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout

class Card(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Violet — Şimdi çalıyor')
        self.setWindowFlags(Qt.WindowType.Tool|Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(500,198);self.setMinimumSize(360,198)
        self.setStyleSheet('QLabel {color:#ece4f8;background:transparent;} QPushButton {background:#352a46;color:#c5b4ff;border:0;border-radius:10px;padding:9px;} QPushButton:hover {background:#584172;}')
        row=QHBoxLayout(self);row.setContentsMargins(20,20,20,20);row.setSpacing(18)
        self.cover=QLabel('♪');self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter);self.cover.setFixedSize(112,112);self.cover.setStyleSheet('background:#30253e;border-radius:14px;color:#c5b4ff;font-size:36px;');row.addWidget(self.cover)
        col=QVBoxLayout();row.addLayout(col,1)
        self.title=QLabel();self.title.setStyleSheet('font-size:19px;font-weight:600;');self.title.setWordWrap(True);col.addWidget(self.title)
        self.artist=QLabel();self.artist.setStyleSheet('color:#aaa1ba;');col.addWidget(self.artist)
        self.lyric=QLabel();self.lyric.setStyleSheet('color:#c5b4ff;');col.addWidget(self.lyric)
        controls=QHBoxLayout();col.addLayout(controls)
        for text,cmd in [('‹','previous'),('▶ / Ⅱ','play-pause'),('›','next')]:
            b=QPushButton(text);b.clicked.connect(lambda checked=False,c=cmd:self.control(c));controls.addWidget(b)
        close=QPushButton('×');close.setFixedSize(32,32);close.clicked.connect(self.close);row.addWidget(close,0,Qt.AlignmentFlag.AlignTop)
        self.art='';self.current={};self.path=Path(os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}'))/'fatih-kingdom/state.json'
        self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(1000);self.refresh()
        screen=QApplication.primaryScreen()
        if screen:
            geo=screen.availableGeometry();self.move(geo.right()-self.width()-24,geo.top()+80)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QColor('#66527e'));p.setBrush(QColor('#17151f'));p.drawRoundedRect(self.rect().adjusted(1,1,-1,-1),22,22)
    def refresh(self):
        presentation=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'violet-desktop/presentation.json'
        try:
            if json.loads(presentation.read_text()).get('enabled'):
                self.current={};self.title.setText('Sunum modu');self.artist.clear();self.lyric.clear();self.cover.clear();self.close();QTimer.singleShot(0,self.close);return
        except (OSError,ValueError):pass
        try:
            if __import__('time').time()-self.path.stat().st_mtime>20:raise OSError('stale')
            state=json.loads(self.path.read_text())
        except (OSError,ValueError):state={}
        self.current=(state.get('providers',{}).get('media',{}).get('data') or {}).get('current') or {}
        for label,text in [(self.title,self.current.get('title') or 'Henüz bir şey çalmıyor'),(self.artist,self.current.get('artist','')),(self.lyric,state.get('lyrics',{}).get('line',''))]:
            label.setTextFormat(Qt.TextFormat.PlainText);label.setText(label.fontMetrics().elidedText(text,Qt.TextElideMode.ElideRight,275))
        path=self.current.get('cover','')
        if path!=self.art:
            self.art=path;self.cover.clear()
            reader=QImageReader(path);reader.setScaledSize(QSize(112,112));image=reader.read() if path else None
            if image is not None and not image.isNull():
                pix=QPixmap(112,112);pix.fill(Qt.GlobalColor.transparent);p=QPainter(pix);p.setRenderHint(QPainter.RenderHint.Antialiasing);clip=QPainterPath();clip.addRoundedRect(0,0,112,112,14,14);p.setClipPath(clip);p.drawImage(pix.rect(),image);p.end();self.cover.setPixmap(pix)
            else:self.cover.setText('♪')
    def control(self,command):
        player=self.current.get('player')
        if player:subprocess.Popen(['playerctl','--player='+player,command],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton and self.windowHandle():self.windowHandle().startSystemMove()
    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_Escape:self.close()
        else:super().keyPressEvent(event)
if __name__=='__main__':
    app=QApplication(sys.argv);app.setApplicationName('kingdom-overlay');widget=Card();widget.show();sys.exit(app.exec())
