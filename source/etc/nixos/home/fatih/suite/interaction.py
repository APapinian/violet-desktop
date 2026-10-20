"""Ephemeral search and a drop surface; private data is never cached on disk."""
import json
from pathlib import Path
from PyQt6.QtCore import Qt,QTimer,QThreadPool
from PyQt6.QtGui import QShortcut,QKeySequence,QIcon
from PyQt6.QtWidgets import *
from common import request,read,STATE,RUNTIME
import productivity as p

class Palette(QWidget):
    def __init__(self):
        super().__init__();self.setWindowTitle('Violet · Komut paleti');self.resize(740,540);self.jobs=set();self.generation=0;self.brain_pending=False;self.present=False;l=QVBoxLayout(self);l.setContentsMargins(28,28,28,24);l.setSpacing(18);title=QLabel('✦  Krallığın komutları');title.setStyleSheet('font-size:22px;color:#c5b4ff');l.addWidget(title);self.query=QLineEdit();self.query.setMaxLength(256);self.query.setPlaceholderText('Uygulama, dosya, ayar, komut, açık MyBrain kaydı…');l.addWidget(self.query);self.query.setMinimumHeight(54);self.results=QListWidget();self.results.setSpacing(5);l.addWidget(self.results,1);self.status=QLabel('Dosya klasörlerini ve kayıtlı komutları Masaüstü ayarlarından seç.');self.status.setWordWrap(True);l.addWidget(self.status);self.debounce=QTimer(self);self.debounce.setSingleShot(True);self.debounce.setInterval(180);self.debounce.timeout.connect(self.search);self.query.textChanged.connect(self.changed);self.query.returnPressed.connect(self.open);self.results.itemActivated.connect(self.open);QShortcut(QKeySequence('Escape'),self,activated=self.close);QShortcut(QKeySequence('Down'),self.query,activated=lambda:self.results.setFocus());self.watch=QTimer(self);self.watch.timeout.connect(self.check_private);self.watch.start(400);self.search();self.query.setFocus()
    def work(self,fn,done):
        from gui import Job
        job=Job(fn);self.jobs.add(job)
        def finish(value,error):
            self.jobs.discard(job)
            if error:self.status.setText(str(error))
            else:done(value)
        job.result.done.connect(finish);QThreadPool.globalInstance().start(job)
    def changed(self):self.generation+=1;self.results.clear();self.debounce.start()
    def search(self):
        token=self.generation;query=self.query.text();brain_start=read(RUNTIME/'brain-state.json',{})
        def done(rows):
            if token!=self.generation or self.present:return
            self.results.clear()
            # A second lock check prevents a search started before lock from restoring stale titles.
            brain_now=read(RUNTIME/'brain-state.json',{});brain=brain_now==brain_start and not brain_now.get('locked',True)
            for row in rows:
                if row['kind']=='brain' and not brain:continue
                item=QListWidgetItem(row['label']+'\n'+row['detail']);item.setData(Qt.ItemDataRole.UserRole,row);self.results.addItem(item)
            if rows:self.results.setCurrentRow(0)
        self.work(lambda:p.palette(query),done)
    def check_private(self):
        self.present=bool(read(STATE/'presentation.json',{}).get('enabled'))
        if self.present:self.generation+=1;self.query.clear();self.results.clear();self.close();return
        if self.brain_pending:return
        self.brain_pending=True
        def task():
            try:return not request('brain','status')['locked']
            except (OSError,ValueError):return False
        def done(unlocked):
            self.brain_pending=False
            if not unlocked:
                for i in range(self.results.count()-1,-1,-1):
                    if self.results.item(i).data(Qt.ItemDataRole.UserRole)['kind']=='brain':self.results.takeItem(i)
        self.work(task,done)
    def open(self,*_):
        item=self.results.currentItem()
        if item:self.work(lambda:p.activate(item.data(Qt.ItemDataRole.UserRole)),lambda _:self.close())
    def closeEvent(self,e):self.generation+=1;self.results.clear();self.query.clear();self.watch.stop();super().closeEvent(e)

class Drop(QWidget):
    def __init__(self):
        super().__init__();self.setWindowTitle('Violet · Dosya işlem alanı');self.setAcceptDrops(True);self.resize(450,410);self.paths=[];self.jobs=set();l=QVBoxLayout(self);title=QLabel('◇  Dosyalarını buraya bırak');title.setStyleSheet('font-size:22px;color:#c5b4ff');l.addWidget(title);self.files=QListWidget();l.addWidget(self.files,1);self.kind=QComboBox()
        for label,kind in [('ZIP oluştur','zip'),('Görselleri PNG’ye dönüştür','png'),('Seçili telefona gönder','phone'),('MyBrain’e şifreli ekle','brain')]:self.kind.addItem(label,kind)
        l.addWidget(self.kind);self.destination=QLineEdit(str(Path.home()/'Downloads'));l.addWidget(self.destination);row=QHBoxLayout();l.addLayout(row);pick=QPushButton('Hedef klasör');pick.clicked.connect(self.folder);row.addWidget(pick);choose=QPushButton('Dosya seç');choose.clicked.connect(self.choose);row.addWidget(choose);apply=QPushButton('İşlemi uygula');apply.clicked.connect(self.apply);row.addWidget(apply);self.status=QLabel('Kaynak dosyalar korunur. Telefon ve MyBrain hedefi önceden seçilmeli / açık olmalı.');self.status.setWordWrap(True);l.addWidget(self.status);QShortcut(QKeySequence('Escape'),self,activated=self.close);self.watch=QTimer(self);self.watch.timeout.connect(lambda:self.close() if read(STATE/'presentation.json',{}).get('enabled') else None);self.watch.start(500)
    def folder(self):
        path=QFileDialog.getExistingDirectory(self,'Hedef klasör')
        if path:self.destination.setText(path)
    def choose(self):
        paths,_=QFileDialog.getOpenFileNames(self,'Dosyalar')
        if paths:self.set_paths(paths)
    def set_paths(self,paths):self.paths=list(dict.fromkeys(paths))[:200];self.files.clear();self.files.addItems([Path(x).name for x in self.paths])
    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls() and all(u.isLocalFile() for u in e.mimeData().urls()):e.acceptProposedAction()
    def dropEvent(self,e):self.set_paths([u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]);e.acceptProposedAction()
    def apply(self):
        from gui import Job
        paths=list(self.paths);kind=self.kind.currentData();destination=self.destination.text();job=Job(lambda:p.drop_files(paths,kind,destination));self.jobs.add(job)
        def finish(value,error):self.jobs.discard(job);self.status.setText(str(error) if error else str(value))
        job.result.done.connect(finish);QThreadPool.globalInstance().start(job)
    def closeEvent(self,e):self.paths=[];self.files.clear();self.watch.stop();super().closeEvent(e)

class QuickNote(QDialog):
    def __init__(self):
        super().__init__();self.setWindowTitle('Violet · Hızlı not');self.resize(530,440);self.jobs=set();l=QVBoxLayout(self);self.title=QLineEdit('Hızlı not');l.addWidget(self.title);self.body=QTextEdit();self.body.setPlaceholderText('Açık MyBrain kasasına yaz…');l.addWidget(self.body,1);self.status=QLabel('Not yalnız şifreli kasaya kaydedilir.');l.addWidget(self.status);self.save_button=QPushButton('MyBrain’e kaydet');self.save_button.clicked.connect(self.save);l.addWidget(self.save_button);self.was_unlocked=False;QShortcut(QKeySequence('Escape'),self,activated=self.close);self.watch=QTimer(self);self.watch.timeout.connect(self.check_lock);self.watch.start(400);self.check_lock()
    def check_lock(self):
        unlocked=not read(RUNTIME/'brain-state.json',{}).get('locked',True)
        if read(STATE/'presentation.json',{}).get('enabled') or self.was_unlocked and not unlocked:self.close();return
        self.was_unlocked=unlocked;self.save_button.setEnabled(unlocked)
        if not unlocked:self.status.setText('Kaydetmek için MyBrain kasasını aç.')
        elif self.status.text()=='Kaydetmek için MyBrain kasasını aç.':self.status.setText('Not yalnız şifreli kasaya kaydedilir.')
    def save(self):
        from gui import Job
        title=self.title.text();body=self.body.toPlainText();job=Job(lambda:request('brain','quick-note',title=title,body=body));self.jobs.add(job)
        def done(value,error):
            self.jobs.discard(job)
            if error:self.status.setText(str(error))
            else:self.body.clear();self.accept()
        job.result.done.connect(done);QThreadPool.globalInstance().start(job)
    def closeEvent(self,e):self.body.clear();self.title.clear();self.watch.stop();super().closeEvent(e)
