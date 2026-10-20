#!/usr/bin/env python3
"""Native Qt desktop for existing encrypted MyBrain collections."""
import calendar, copy, datetime as dt, json, os, subprocess, sys, uuid
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut, QPainter, QColor, QLinearGradient, QFont
from PyQt6.QtWidgets import (QApplication,QMainWindow,QWidget,QLabel,QPushButton,QLineEdit,QVBoxLayout,QHBoxLayout,QStackedWidget,QListWidget,QListWidgetItem,QFileDialog,QMessageBox,QDialog,QFormLayout,QScrollArea,QTextEdit,QComboBox,QDoubleSpinBox,QCheckBox,QTableWidget,QTableWidgetItem,QCalendarWidget,QSplitter)
from vault import Vault, atomic
META=json.loads(Path(__file__).with_name('schema.json').read_text())
STYLE=Path(__file__).with_name('violet.qss').read_text()

def title(row):return str(row.get('title') or row.get('front') or row.get('date') or row.get('language') or 'Kayıt')
def text(row):return str(row.get('body') or row.get('review') or row.get('learned') or row.get('note') or row.get('back') or '')
def today():return dt.date.today().isoformat()

class Editor(QDialog):
    def __init__(self,parent,key,record):
        super().__init__(parent);self.parentWindow=parent;self.key=key;self.record=copy.deepcopy(record);self.inputs={};self.setWindowTitle('MyBrain · Kayıt');self.resize(680,720)
        outer=QVBoxLayout(self);scroll=QScrollArea();scroll.setWidgetResizable(True);body=QWidget();form=QFormLayout(body);scroll.setWidget(body);outer.addWidget(scroll)
        for spec in META['schema'][key]:
            name,label=spec[:2];kind=spec[2] if len(spec)>2 else '';value=record.get(name,'')
            if kind=='textarea':w=QTextEdit(str(value));w.setMinimumHeight(110)
            elif kind=='number':
                w=QDoubleSpinBox();w.setRange(-1e9,1e9);w.setDecimals(2);w.setValue(float(value or 0))
            elif kind.startswith('select:'):
                w=QComboBox();w.addItems(kind[7:].split('|'))
                if value and w.findText(str(value))<0:w.addItem(str(value))
                if value:w.setCurrentText(str(value))
            else:w=QLineEdit(', '.join(value) if isinstance(value,list) else str(value or (today() if kind=='date' else '')))
            self.inputs[name]=(w,kind);form.addRow(label,w)
        if key=='tasks':
            w=QCheckBox('Tamamlandı');w.setChecked(record.get('completed',False));self.inputs['completed']=(w,'bool');form.addRow(w)
        row=QHBoxLayout();outer.addLayout(row)
        for label,callback in [('Ek dosya',self.attach),('Kaydet',self.accept_record),('Vazgeç',self.reject)]:b=QPushButton(label);b.clicked.connect(callback);row.addWidget(b)
        self.assetLabel=QLabel('');outer.addWidget(self.assetLabel)
    def attach(self):
        path=QFileDialog.getOpenFileName(self,'Ek dosya seç')[0]
        if not path:return
        try:
            ref=self.parentWindow.vault.put_asset(path)
            field={'library':'file_path','documents':'file_path','health':'photo_path'}.get(self.key,'attachments')
            if field=='attachments':self.record.setdefault(field,[]).append(ref)
            else:self.record[field]=ref
            self.assetLabel.setText(Path(path).name+' şifrelendi')
        except Exception as e:QMessageBox.warning(self,'Eklenemedi',str(e))
    def accept_record(self):
        record=copy.deepcopy(self.record)
        for name,(w,kind) in self.inputs.items():
            value=w.toPlainText() if kind=='textarea' else w.value() if kind=='number' else w.isChecked() if kind=='bool' else w.currentText() if kind.startswith('select:') else w.text()
            if name=='tags':value=[x.strip() for x in value.split(',') if x.strip()]
            record[name]=int(value) if name in ('priority','mood','rating','calories','steps','duration_minutes','correct','wrong','empty','minutes','word_count') and kind=='number' else value
        record.setdefault('id',str(uuid.uuid4()))
        defaults={'notes':{'attachments':[]},'journal':{'attachments':[]},'language_logs':{'attachments':[]},'events':{'task_ids':[]},'library':{'file_path':'','cover_path':''},'media':{'external_id':'','poster_path':''},'health':{'photo_path':''},'documents':{'file_path':''}}
        for k,v in defaults.get(self.key,{}).items():record.setdefault(k,v)
        for k,v in {'tasks':{'completed':False,'goal_id':None},'habits':{'completed_dates':[]},'flashcards':{'repetitions':0,'interval_days':1,'ease':2.5}}.get(self.key,{}).items():record.setdefault(k,v)
        data=copy.deepcopy(self.parentWindow.data);items=data.setdefault(self.key,[])
        idx=next((i for i,x in enumerate(items) if x.get('id')==record['id']),None)
        if idx is None:items.append(record)
        else:items[idx]=record
        if self.parentWindow.commit(data):self.accept()

class PalaceHeader(QWidget):
    def __init__(self):
        super().__init__();self.setMinimumHeight(130)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient=QLinearGradient(0,0,self.width(),self.height());gradient.setColorAt(0,QColor('#34264d'));gradient.setColorAt(1,QColor('#171822'))
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(gradient);p.drawRoundedRect(self.rect(),24,24)
        p.setPen(QColor('#7d639e'))
        for x,y in [(20,20),(self.width()-20,20),(20,self.height()-20),(self.width()-20,self.height()-20)]:
            p.drawLine(x-7,y,x+7,y);p.drawLine(x,y-7,x,y+7)
        p.setFont(QFont('DejaVu Serif',24));p.setPen(QColor('#e8ddff'));p.drawText(34,65,'MyBrain  ·  Zihinsel saray')
        p.setFont(QFont('Rubik',11));p.setPen(QColor('#b4a4c9'));p.drawText(36,98,'Düşünceler · Bağlantılar · Hatıralar')

class Brain(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('MyBrain · Violet');self.resize(1280,850);self.setMinimumSize(820,580);self.data={};self.vault=None;self.key='home';self.ids=[]
        self.stack=QStackedWidget();self.setCentralWidget(self.stack);self.gate=self.make_gate();self.stack.addWidget(self.gate);self.desktop=self.make_desktop();self.stack.addWidget(self.desktop)
        QShortcut(QKeySequence('Ctrl+K'),self,activated=lambda:self.search.setFocus());QShortcut(QKeySequence('Ctrl+L'),self,activated=self.lock)
        self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.focusRemaining=0;self.timer.start(1000)
        self.idle=QTimer(self);self.idle.setInterval(10*60*1000);self.idle.setSingleShot(True);self.idle.timeout.connect(self.lock)
        QApplication.instance().installEventFilter(self)
    def eventFilter(self,obj,event):
        from PyQt6.QtCore import QEvent
        if self.vault and event.type() in (QEvent.Type.KeyPress,QEvent.Type.MouseButtonPress,QEvent.Type.TouchBegin,QEvent.Type.TouchUpdate,QEvent.Type.TabletPress,QEvent.Type.TabletMove):self.idle.start()
        return super().eventFilter(obj,event)
    def make_gate(self):
        root=QWidget();layout=QVBoxLayout(root);layout.setContentsMargins(120,90,120,90);layout.addStretch()
        layout.addWidget(PalaceHeader());h=QLabel('Kasana gir');h.setObjectName('hero');layout.addWidget(h);layout.addWidget(QLabel('Fatih’in zihinsel sarayı · Şifreli, taşınabilir, yerel'))
        preferred=os.environ.get('MYBRAIN_DATA_DIR','/run/media/fatih/Ventoy/MyBrain')
        self.path=QLineEdit(preferred);self.path.setPlaceholderText('MyBrain klasörünü seç');layout.addWidget(self.path)
        choose=QPushButton('Kasa klasörünü seç');choose.clicked.connect(self.choose);layout.addWidget(choose)
        self.password=QLineEdit();self.password.setEchoMode(QLineEdit.EchoMode.Password);self.password.setPlaceholderText('Ana parola');self.password.returnPressed.connect(lambda:self.unlock(False));layout.addWidget(self.password)
        row=QHBoxLayout();layout.addLayout(row)
        for name,create in [('Kasayı aç',False),('Yeni kasa oluştur',True)]:b=QPushButton(name);b.clicked.connect(lambda checked=False,c=create:self.unlock(c));row.addWidget(b)
        note=QLabel('Rust sürümü açıksa kaydetmeden önce kapat. Python aynı şifreli kasayı kullanır.');note.setWordWrap(True);layout.addWidget(note);layout.addStretch();return root
    def choose(self):
        path=QFileDialog.getExistingDirectory(self,'MyBrain klasörü',str(Path.home()))
        if path:self.path.setText(path)
    def unlock(self,create):
        if not self.path.text().strip() or not self.password.text():return
        try:
            vault=Vault(self.path.text(),self.password.text())
            if create:vault.create(META['schema'])
            else:vault.load()
            self.vault=vault;
            from desktop_ipc import publish
            publish(False)
            self.data=copy.deepcopy(vault.data);self.password.clear();self.stack.setCurrentIndex(1);self.idle.start();self.navigate('home');self.statusBar().showMessage(f'{vault.root} · Revision {vault.manifest["revision"]}')
        except Exception as e:QMessageBox.warning(self,'Kasa açılamadı',str(e))
    def make_desktop(self):
        root=QWidget();layout=QHBoxLayout(root);layout.setContentsMargins(0,0,0,0)
        self.nav=QListWidget();self.nav.setFixedWidth(256);layout.addWidget(self.nav)
        self.sections=[('home','✦  Saray')]+[(k,v) for k,v,_ in META['sections']]+[('calendar','Takvim'),('reports','Raporlar'),('graph','Bağlantılar'),('focus','Odak odası')]
        for key,label in self.sections:item=QListWidgetItem(label);item.setData(Qt.ItemDataRole.UserRole,key);self.nav.addItem(item)
        self.nav.currentItemChanged.connect(lambda item,old:self.navigate(item.data(Qt.ItemDataRole.UserRole)) if item else None)
        main=QWidget();content=QVBoxLayout(main);content.setContentsMargins(32,28,32,28);content.setSpacing(16);content.addWidget(PalaceHeader());layout.addWidget(main,1)
        header=QHBoxLayout();content.addLayout(header);self.heading=QLabel('Saray');self.heading.setObjectName('hero');header.addWidget(self.heading,1)
        lock=QPushButton('Kilitle');lock.clicked.connect(self.lock);header.addWidget(lock)
        self.search=QLineEdit();self.search.setPlaceholderText('Kasada ara · Ctrl+K');self.search.textChanged.connect(self.render);content.addWidget(self.search)
        actions=QHBoxLayout();content.addLayout(actions)
        for label,fn in [('Yeni kayıt',self.add),('Düzenle',self.edit),('Sil',self.delete),('Eki dışa aktar',self.export_asset),('JSON dışa aktar',self.export_json)]:b=QPushButton(label);b.clicked.connect(fn);actions.addWidget(b)
        self.pages=QStackedWidget();content.addWidget(self.pages,1)
        self.table=QTableWidget();self.table.setColumnCount(3);self.table.setHorizontalHeaderLabels(['Başlık','Tarih / durum','İçerik']);self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows);self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection);self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.table.doubleClicked.connect(self.edit);self.table.setAlternatingRowColors(True);self.pages.addWidget(self.table)
        self.summary=QTextEdit();self.summary.setReadOnly(True);self.pages.addWidget(self.summary)
        cal=QWidget();c=QVBoxLayout(cal);self.calendar=QCalendarWidget();c.addWidget(self.calendar);self.calendarText=QTextEdit();self.calendarText.setReadOnly(True);c.addWidget(self.calendarText);self.calendar.selectionChanged.connect(self.show_calendar);self.pages.addWidget(cal)
        self.focus=QWidget();f=QVBoxLayout(self.focus);self.focusLabel=QLabel('25:00');self.focusLabel.setObjectName('hero');f.addWidget(self.focusLabel)
        for label,seconds in [('25 dakika çalış',1500),('5 dakika mola',300),('Durdur',0)]:b=QPushButton(label);b.clicked.connect(lambda checked=False,s=seconds:self.set_focus(s));f.addWidget(b)
        f.addStretch();self.pages.addWidget(self.focus);return root
    def navigate(self,key):
        self.key=key;self.heading.setText(dict(self.sections).get(key,key));self.render()
    def render(self,*args):
        if not self.vault:return
        query=self.search.text().casefold().strip()
        if self.key=='calendar' and not query:self.pages.setCurrentIndex(2);self.show_calendar();return
        if self.key=='focus' and not query:self.pages.setCurrentIndex(3);return
        if self.key in ('home','reports','graph') and not query:
            self.pages.setCurrentIndex(1);self.summary.setPlainText(self.report(self.key));return
        self.pages.setCurrentIndex(0);rows=[]
        keys=META['schema'] if query else [self.key]
        for key in keys:
            for item in self.data.get(key,[]):
                if not isinstance(item,dict):continue
                if query and query not in json.dumps(item,ensure_ascii=False).casefold():continue
                rows.append((key,item))
        self.ids=[(key,row.get('id')) for key,row in rows];self.table.setRowCount(len(rows))
        for i,(key,row) in enumerate(rows):
            for j,value in enumerate([title(row),row.get('date') or row.get('due_date') or row.get('status') or ('✓' if row.get('completed') else ''),text(row)[:220]]):self.table.setItem(i,j,QTableWidgetItem(str(value)))
        self.table.setColumnWidth(0,270);self.table.setColumnWidth(1,160);self.table.horizontalHeader().setStretchLastSection(True)
    def selected(self):
        row=self.table.currentRow()
        if 0<=row<len(self.ids):
            key,ident=self.ids[row];item=next((x for x in self.data.get(key,[]) if x.get('id')==ident),None)
            return key,item
        return None,None
    def add(self):
        if self.vault:Editor(self,self.key if self.key in META['schema'] else 'notes',{}).exec()
    def edit(self,*args):
        key,row=self.selected()
        if row:Editor(self,key,row).exec()
    def commit(self,data):
        try:self.vault.save(data);self.data=copy.deepcopy(data);self.render();self.statusBar().showMessage('Kaydedildi · Revision '+str(self.vault.manifest['revision']));return True
        except Exception as e:QMessageBox.warning(self,'Kaydedilemedi',str(e));return False
    def delete(self):
        key,row=self.selected()
        if row and QMessageBox.question(self,'Kaydı sil',f'{title(row)} silinsin mi?')==QMessageBox.StandardButton.Yes:
            data=copy.deepcopy(self.data);data[key]=[x for x in data[key] if x.get('id')!=row['id']];self.commit(data)
    def export_asset(self):
        key,row=self.selected()
        if not row:return
        refs=[x for x in row.get('attachments',[]) if isinstance(x,str) and x.startswith('asset:')]
        refs += [row[x] for x in ('file_path','photo_path','cover_path','poster_path') if isinstance(row.get(x),str) and row[x].startswith('asset:')]
        if not refs:QMessageBox.information(self,'Ek dosya','Bu kayıtta şifreli ek dosya yok.');return
        from PyQt6.QtWidgets import QInputDialog
        ref,ok=QInputDialog.getItem(self,'Ek dosya','Dışa aktarılacak dosya',refs,editable=False)
        if not ok:return
        target=QFileDialog.getSaveFileName(self,'Eki dışa aktar',ref.split(':',2)[2])[0]
        if target:
            try:atomic(target,self.vault.get_asset(ref))
            except Exception as e:QMessageBox.warning(self,'Dışa aktarılamadı',str(e))
    def export_json(self):
        if not self.vault:return
        target=QFileDialog.getSaveFileName(self,'Şifresiz JSON dışa aktar','mybrain-export.json','JSON (*.json)')[0]
        if target:
            try:atomic(target,json.dumps(self.data,ensure_ascii=False,indent=2).encode());self.statusBar().showMessage('JSON dışa aktarıldı')
            except Exception as e:QMessageBox.warning(self,'Dışa aktarılamadı',str(e))
    def report(self,key):
        if key=='graph':
            rows=[]
            for collection in META['schema']:
                for record in self.data.get(collection,[]):
                    if not isinstance(record,dict):continue
                    import re
                    links=re.findall(r'\[\[([^\]]+)\]\]',json.dumps(record,ensure_ascii=False))
                    for link in links:rows.append(title(record)+' → '+link)
            return 'Kayıt bağlantıları\n\n'+'\n'.join(rows or ['[[Kayıt başlığı]] biçimindeki bağlantılar burada görünür.'])
        tasks=self.data.get('tasks',[]);complete=sum(bool(x.get('completed')) for x in tasks);health=sorted(self.data.get('health',[]),key=lambda x:x.get('date',''));languages=self.data.get('language_logs',[])
        lines=['Hoş geldin, Fatih',today(),'','Görevler: '+str(complete)+' / '+str(len(tasks))+' tamamlandı','Dil çalışması: '+str(sum(float(x.get('minutes') or 0) for x in languages))+' dakika']
        if health:lines += ['Son kilo: '+str(health[-1].get('weight_kg','—'))+' kg','İlk → son kilo: '+str(health[0].get('weight_kg','—'))+' → '+str(health[-1].get('weight_kg','—'))]
        lines += ['','Koleksiyonlar']+[label+': '+str(len(self.data.get(k,[]))) for k,label,_ in META['sections']]
        if key=='reports':
            lines+=['','Son 7 / 30 / 90 gün']
            for days in (7,30,90):
                cutoff=(dt.date.today()-dt.timedelta(days=days-1)).isoformat();count=sum(1 for k in META['schema'] for x in self.data.get(k,[]) if isinstance(x,dict) and cutoff<=str(x.get('date',''))<=today())
                lines.append(str(days)+' gün: '+str(count)+' tarihli kayıt')
        return '\n'.join(lines)
    def show_calendar(self):
        if not self.vault:return
        date=self.calendar.selectedDate().toString('yyyy-MM-dd');lines=[date,'']
        for k,label,_ in META['sections']:
            for row in self.data.get(k,[]):
                if row.get('date')==date or row.get('due_date')==date:lines.append(label+' · '+title(row))
        self.calendarText.setPlainText('\n'.join(lines))
    def set_focus(self,seconds):self.focusRemaining=seconds;self.tick()
    def tick(self):
        if self.focusRemaining>0:
            self.focusRemaining-=1
            if self.focusRemaining==0:subprocess.Popen(['notify-send','MyBrain','Odak süresi tamamlandı'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.focusLabel.setText(f'{self.focusRemaining//60:02}:{self.focusRemaining%60:02}')
        if self.vault and not (self.vault.root/'vault.json').exists():self.lock();self.statusBar().showMessage('USB çıkarıldı; kasa kilitlendi')
    def closeEvent(self,event):
        self.lock();super().closeEvent(event)
    def lock(self):
        from desktop_ipc import publish
        publish(True)
        for dialog in self.findChildren(QDialog):dialog.reject();dialog.deleteLater()
        self.idle.stop();self.vault=None;self.data={};self.focusRemaining=0;self.table.setRowCount(0);self.summary.clear();self.calendarText.clear();self.search.clear();self.password.clear();self.stack.setCurrentIndex(0);self.statusBar().showMessage('Kasa kilitli')
if __name__=='__main__':
    import argparse
    from desktop_ipc import BrainServer,forward
    parser=argparse.ArgumentParser();parser.add_argument('--vault',default='');args=parser.parse_args()
    app=QApplication(sys.argv);app.setApplicationName('mybrain-python');app.setStyle('Fusion');app.setStyleSheet(STYLE)
    if forward(args.vault):sys.exit(0)
    if args.vault:os.environ['MYBRAIN_DATA_DIR']=args.vault
    window=Brain();window.desktop_ipc=BrainServer(window);window.show();sys.exit(app.exec())
