"""Wayland screenshot-based pen canvas, live region magnifier, color picker."""
import math,subprocess
from pathlib import Path
from PyQt6.QtCore import Qt,QPointF,QRectF,QTimer,QProcess,QBuffer,QByteArray,QIODevice
from PyQt6.QtGui import QImage,QPainter,QPen,QColor,QShortcut,QKeySequence
from PyQt6.QtWidgets import QWidget,QMainWindow,QVBoxLayout,QHBoxLayout,QPushButton,QComboBox,QLabel,QFileDialog,QSpinBox,QMessageBox,QCheckBox
from backend import run
from common import update

def selected(point=False):return run(['slurp','-p'] if point else ['slurp']).strip()

def capture(region):
    result=subprocess.run(['grim','-g',region,'-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=8)
    if result.returncode:raise ValueError(result.stderr.decode(errors='replace')[:300])
    image=QImage.fromData(result.stdout,'PNG')
    if image.isNull():raise ValueError('Ekran görüntüsü alınamadı')
    return image

def image_bytes(image):
    raw=QByteArray();buffer=QBuffer(raw);buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG');return bytes(raw)

def copy_image(image):
    p=subprocess.run(['wl-copy','--type','image/png'],input=image_bytes(image),stderr=subprocess.PIPE,timeout=5)
    if p.returncode:raise ValueError(p.stderr.decode(errors='replace'))

class Canvas(QWidget):
    def __init__(self,image):
        super().__init__();self.base=image;self.strokes=[];self.current=None;self.tool='Kalem';self.color=QColor('#b9a3ff');self.penwidth=5;self.setMinimumSize(500,350)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents,True)
    def rect(self):
        ratio=min(self.width()/self.base.width(),self.height()/self.base.height());w=self.base.width()*ratio;h=self.base.height()*ratio
        return QRectF((self.width()-w)/2,(self.height()-h)/2,w,h)
    def point(self,pos):
        rect=self.rect();return QPointF(max(0,min(self.base.width(),(pos.x()-rect.x())*self.base.width()/rect.width())),max(0,min(self.base.height(),(pos.y()-rect.y())*self.base.height()/rect.height())))
    def draw(self,painter,strokes):
        for stroke in strokes:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear if stroke['tool']=='Silgi' else QPainter.CompositionMode.CompositionMode_SourceOver)
            points=stroke['points'];painter.setPen(QPen(QColor(stroke['color']),stroke['width'],Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin))
            if not points:continue
            if stroke['tool']=='Dikdörtgen':painter.drawRect(QRectF(points[0],points[-1]).normalized())
            elif stroke['tool']=='Ok':
                start,end=points[0],points[-1];painter.drawLine(start,end);angle=math.atan2(end.y()-start.y(),end.x()-start.x());length=max(15,stroke['width']*4)
                for delta in (-.5,.5):painter.drawLine(end,QPointF(end.x()-length*math.cos(angle+delta),end.y()-length*math.sin(angle+delta)))
            elif len(points)==1:painter.drawPoint(points[0])
            else:
                for a,b in zip(points,points[1:]):painter.drawLine(a,b)
    def layer(self,strokes):
        layer=QImage(self.base.size(),QImage.Format.Format_ARGB32_Premultiplied);layer.fill(Qt.GlobalColor.transparent);painter=QPainter(layer);painter.setRenderHint(QPainter.RenderHint.Antialiasing);self.draw(painter,strokes);painter.end();return layer
    def output(self):
        out=self.base.copy();painter=QPainter(out);painter.drawImage(0,0,self.layer(self.strokes));painter.end();return out
    def paintEvent(self,event):
        painter=QPainter(self);painter.fillRect(self.rect().adjusted(-self.width(),-self.height(),self.width(),self.height()),QColor('#14121d'));rect=self.rect();painter.drawImage(rect,self.base);painter.drawImage(rect,self.layer(self.strokes+([self.current] if self.current else [])))
    def begin(self,pos,pressure=1):self.current={'tool':self.tool,'color':self.color.name(),'width':self.penwidth*max(.3,pressure),'points':[self.point(pos)]};self.update()
    def move(self,pos):
        if self.current:self.current['points'].append(self.point(pos));self.update()
    def end(self):
        if self.current:self.strokes.append(self.current);self.current=None;self.update()
    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton:self.begin(e.position())
    def mouseMoveEvent(self,e):self.move(e.position())
    def mouseReleaseEvent(self,e):self.end()
    def tabletEvent(self,e):
        from PyQt6.QtCore import QEvent
        if e.type()==QEvent.Type.TabletPress:self.begin(e.position(),e.pressure())
        elif e.type()==QEvent.Type.TabletMove:self.move(e.position())
        elif e.type()==QEvent.Type.TabletRelease:self.end()
        e.accept()
    def undo(self):
        if self.strokes:self.strokes.pop();self.update()

class Annotation(QMainWindow):
    def __init__(self,image):
        super().__init__();self.setWindowTitle('Violet · Ekran çizimi');self.resize(1100,760);self.canvas=Canvas(image);root=QWidget();layout=QVBoxLayout(root);toolbar=QHBoxLayout();layout.addLayout(toolbar);layout.addWidget(self.canvas,1);self.setCentralWidget(root)
        tool=QComboBox();self.tool=tool;tool.addItems(['Kalem','Ok','Dikdörtgen','Silgi']);tool.currentTextChanged.connect(lambda value:setattr(self.canvas,'tool',value));toolbar.addWidget(tool)
        colors=QComboBox();colors.addItems(['#b9a3ff','#ffffff','#ffcf77','#ff718c','#67dcc5']);colors.currentTextChanged.connect(lambda v:setattr(self.canvas,'color',QColor(v)));toolbar.addWidget(colors)
        width=QSpinBox();width.setRange(1,25);width.setValue(5);width.valueChanged.connect(lambda v:setattr(self.canvas,'penwidth',v));toolbar.addWidget(width)
        for title,fn in [('Geri al',self.canvas.undo),('Kopyala',lambda:copy_image(self.canvas.output())),('PNG kaydet',self.save),('Tam ekran',lambda:self.showNormal() if self.isFullScreen() else self.showFullScreen()),('Kapat',self.close)]:
            btn=QPushButton(title);btn.clicked.connect(lambda _,f=fn:self.guard(f));toolbar.addWidget(btn)
        QShortcut(QKeySequence('Ctrl+Z'),self,activated=self.canvas.undo);QShortcut(QKeySequence('Escape'),self,activated=self.close)
    def guard(self,fn):
        try:fn()
        except Exception as e:QMessageBox.warning(self,'Çizim',str(e))
    def save(self):
        path,_=QFileDialog.getSaveFileName(self,'Çizimi kaydet',str(Path.home()/'Pictures/ekran-cizimi.png'),'PNG (*.png)')
        if path and not self.canvas.output().save(path,'PNG'):raise ValueError('Görsel kaydedilemedi')

class Magnifier(QWidget):
    def __init__(self,region):
        super().__init__();self.region=region;self.setWindowTitle('Violet · Büyüteç');self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint);self.resize(650,430);layout=QVBoxLayout(self);row=QHBoxLayout();layout.addLayout(row)
        label=QLabel('Seçilen alan · canlı');row.addWidget(label);button=QPushButton('Alan seç');button.clicked.connect(self.select);row.addWidget(button);close=QPushButton('Kapat');close.clicked.connect(self.close);row.addWidget(close)
        self.follow=QCheckBox('İmleci takip et');row.addWidget(self.follow);self.zoom=QSpinBox();self.zoom.setRange(2,8);self.zoom.setValue(3);row.addWidget(self.zoom)
        self.pointer=QProcess(self);self.pointer.finished.connect(self.pointer_finished)
        self.view=QLabel();self.view.setAlignment(Qt.AlignmentFlag.AlignCenter);layout.addWidget(self.view,1);self.proc=QProcess(self);self.proc.finished.connect(self.finished);self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(350);self.refresh();QShortcut(QKeySequence('Escape'),self,activated=self.close)
    def refresh(self):
        if self.proc.state()!=QProcess.ProcessState.NotRunning:return
        if self.follow.isChecked():
            if self.pointer.state()==QProcess.ProcessState.NotRunning:self.pointer.start('violet-desktop-pointer',[])
        else:self.proc.start('grim',['-g',self.region,'-'])
    def pointer_finished(self,code,status):
        import json
        try:
            value=json.loads(bytes(self.pointer.readAllStandardOutput()));x,y=value['x'],value['y'];screen=next(s for s in value['screens'] if s['x']<=x<s['x']+s['width'] and s['y']<=y<s['y']+s['height'])
            # Freeze when hovering the magnifier itself to avoid recursive captures.
            if self.geometry().contains(int(x),int(y)):return
            width=min(screen['width'],max(40,self.view.width()//self.zoom.value()));height=min(screen['height'],max(30,self.view.height()//self.zoom.value()))
            left=max(screen['x'],min(int(x-width/2),screen['x']+screen['width']-width));top=max(screen['y'],min(int(y-height/2),screen['y']+screen['height']-height))
            self.proc.start('grim',['-g',f'{left},{top} {width}x{height}','-'])
        except Exception:self.view.setText('Qtile imleç servisine bağlanılamadı; sabit alan seçimini kullanabilirsin.')
    def finished(self,code,status):
        from PyQt6.QtGui import QPixmap
        raw=bytes(self.proc.readAllStandardOutput());image=QImage.fromData(raw,'PNG')
        if image.isNull():self.view.setText(bytes(self.proc.readAllStandardError()).decode(errors='replace')[:200]);return
        self.view.setPixmap(QPixmap.fromImage(image).scaled(self.view.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.FastTransformation))
    def select(self):
        self.timer.stop();self.hide()
        try:self.region=selected()
        except Exception:pass
        self.show();self.timer.start(350)
    def closeEvent(self,e):self.timer.stop();self.proc.kill();self.pointer.kill();super().closeEvent(e)

def color_pick():
    image=capture(selected(True));color=image.pixelColor(0,0);hexvalue=color.name();rgb=f'rgb({color.red()}, {color.green()}, {color.blue()})'
    subprocess.run(['wl-copy'],input=hexvalue.encode(),check=True,timeout=5)
    update(lambda c:c['palette'].insert(0,{'hex':hexvalue,'rgb':rgb}) if not any(x['hex']==hexvalue for x in c['palette']) else None)
    return hexvalue+' · '+rgb
