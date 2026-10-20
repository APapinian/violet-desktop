"""Violet native desktop center. Operations run off the GUI thread."""
import datetime as dt,json,os,subprocess,sys,uuid
from pathlib import Path
from PyQt6.QtCore import Qt,QObject,pyqtSignal,QRunnable,QThreadPool,QTimer,QSize
from PyQt6.QtGui import QIcon,QShortcut,QKeySequence,QPainter,QPixmap,QLinearGradient,QColor
from PyQt6.QtWidgets import *
from common import CONFIG,STATE,config,update,request,read
from backend import APPS,History,users_of,diagnostics,run,spawn
STYLE='''QWidget {background:#17141f;color:#eee7ff;font:13px "Rubik";} QMainWindow {background:#100e17;} QListWidget,QTableWidget,QTextEdit,QLineEdit,QComboBox,QSpinBox {background:#211c2d;border:1px solid #3d3152;border-radius:8px;padding:8px;} QPushButton {background:#30263f;border:1px solid #514066;border-radius:9px;padding:10px 16px;} QPushButton:hover {background:#4b3864;} QPushButton:disabled {color:#766b89;} QListWidget::item {padding:12px;} QListWidget::item:selected,QTableWidget::item:selected {background:#51406a;} QHeaderView::section {background:#30263f;border:0;padding:9px;} QLabel#hero {font-size:28px;color:#cfbcff;} QTabBar::tab {padding:12px;background:#211c2d;} QScrollBar {background:#211c2d;} QToolTip {background:#30263f;color:#eee7ff;}'''

class Result(QObject):done=pyqtSignal(object,object)
class Job(QRunnable):
    def __init__(self,fn):super().__init__();self.fn=fn;self.result=Result()
    def run(self):
        try:value,error=self.fn(),None
        except Exception as e:value,error=None,e
        self.result.done.emit(value,error)

def table(headers):
    t=QTableWidget(0,len(headers));t.setHorizontalHeaderLabels(headers);t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection);t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);t.verticalHeader().hide();t.setWordWrap(False);return t

def rows(widget,values):
    selected=widget.currentRow();widget.setRowCount(len(values))
    for i,row in enumerate(values):
        for j,value in enumerate(row):widget.setItem(i,j,QTableWidgetItem(str(value)))
    if 0<=selected<len(values):widget.selectRow(selected)

def mb(value):return f'{value/1024/1024:.1f} MiB'

def confirm(parent,text):return QMessageBox.question(parent,'Violet',text)==QMessageBox.StandardButton.Yes

class Hero(QWidget):
    def __init__(self):
        super().__init__();self.setFixedHeight(155);self.art=QPixmap(str(Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'quickshell/fatih/assets/hyrule-violet.png'))
    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.Antialiasing);painter.setPen(Qt.PenStyle.NoPen);painter.setBrush(QColor('#30233f'));painter.drawRoundedRect(self.rect(),18,18)
        if not self.art.isNull():
            painter.setOpacity(.30);painter.drawPixmap(self.rect(),self.art,self.art.rect());painter.setOpacity(1)
        gradient=QLinearGradient(0,0,self.width(),0);gradient.setColorAt(0,QColor('#e020172e'));gradient.setColorAt(1,QColor('#502a1d40'));painter.fillRect(self.rect(),gradient)
        painter.setPen(QColor('#c5b4ff'));font=painter.font();font.setPixelSize(13);font.setLetterSpacing(font.SpacingType.AbsoluteSpacing,4);painter.setFont(font);painter.drawText(26,42,'H Y R U L E')
        font.setLetterSpacing(font.SpacingType.AbsoluteSpacing,0);font.setPixelSize(26);painter.setFont(font);painter.setPen(QColor('#eee7ff'));painter.drawText(26,89,'Masaüstünün kontrolü sende')
        font.setPixelSize(12);painter.setFont(font);painter.setPen(QColor('#b1a1c4'));painter.drawText(26,125,'VIOLET  /  Pencereler · Kalem · Dosyalar · Kurallar')

class RuleDialog(QDialog):
    def __init__(self,parent,state,existing=None):
        super().__init__(parent);self.setWindowTitle('Masaüstü kuralı');self.resize(570,520);form=QFormLayout(self)
        self.name=QLineEdit();form.addRow('Ad',self.name);self.enabled=QCheckBox('Etkin');self.enabled.setChecked(True);form.addRow(self.enabled)
        self.event=QComboBox();self.event.addItem('USB bağlandığında','usb');self.event.addItem('Uygulama başladığında','app');self.event.addItem('Ağa bağlanınca','network');self.event.addItem('Saat geldiğinde','time');form.addRow('Olay',self.event)
        self.value=QComboBox();self.value.setEditable(True);form.addRow('Olay değeri',self.value)
        self.kind=QComboBox()
        for label,kind in [('Uygulama aç','app'),('Kayıtlı düzeni uygula','preset'),('Bildirim göster','notify'),('Uykuyu engelle','awake'),('Sunum modunu aç','presentation'),('USB MyBrain kasasını aç','mybrain'),('USB fotoğraflarını kopyala','photos')]:self.kind.addItem(label,kind)
        form.addRow('İşlem',self.kind);self.app=QComboBox();self.app.addItems(APPS);form.addRow('Uygulama',self.app)
        self.preset=QComboBox()
        for p in config()['presets']:self.preset.addItem(p['name'],p['id'])
        form.addRow('Düzen',self.preset);self.text=QLineEdit('Hatırlatma');form.addRow('Bildirim',self.text);self.minutes=QSpinBox();self.minutes.setRange(1,1440);self.minutes.setValue(30);form.addRow('Dakika',self.minutes)
        self.usb=QComboBox()
        for m in state.get('mounts',[]):
            if m['uuid']:self.usb.addItem(m['label']+' · '+m['uuid'],m['uuid'])
        form.addRow('İşlemin USB cihazı',self.usb);self.relative=QLineEdit('MyBrain');form.addRow('USB içindeki klasör',self.relative)
        self.destination=QLineEdit(str(Path.home()/'Pictures/USB'));form.addRow('Fotoğraf hedefi',self.destination)
        note=QLabel('Olay değeri: USB UUID, uygulama işlem adı, ağ UUID veya HH:MM. Fotoğraflar kopyalanır; kaynaklar silinmez.');note.setWordWrap(True);form.addRow(note)
        self.event.currentIndexChanged.connect(lambda:self.populate(state));self.populate(state)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);form.addRow(buttons)
        self.original=existing or {};a=self.original.get('action',{})
        if existing:
            self.name.setText(existing['name']);self.enabled.setChecked(existing.get('enabled',True));self.event.setCurrentIndex(max(0,self.event.findData(existing['event'])));self.value.setEditText(existing['value']);self.kind.setCurrentIndex(max(0,self.kind.findData(a.get('kind'))));self.app.setCurrentText(a.get('app','Dosyalar'));self.text.setText(a.get('text',''));self.minutes.setValue(int(a.get('minutes',30)));self.relative.setText(a.get('relative','MyBrain'));self.destination.setText(a.get('destination',str(Path.home()/'Pictures/USB')));self.usb.setCurrentIndex(max(0,self.usb.findData(a.get('uuid'))));self.preset.setCurrentIndex(max(0,self.preset.findData(a.get('preset'))))
    def populate(self,state):
        self.value.clear();kind=self.event.currentData()
        if kind=='usb':self.value.addItems([m['uuid'] for m in state.get('mounts',[]) if m['uuid']])
        if kind=='app':self.value.addItems(sorted({p['name'] for p in state.get('metrics',{}).get('processes',[])}))
        if kind=='network':self.value.addItem(state.get('network',''))
        if kind=='time':self.value.addItem('09:00')
    def record(self):
        import re
        event,value=self.event.currentData(),self.value.currentText().strip();kind=self.kind.currentData()
        if not self.name.text().strip() or not value:raise ValueError('Ad ve olay değeri gerekli')
        if event=='time' and not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',value):raise ValueError('Saat HH:MM olmalı')
        action={'kind':kind}
        if kind=='app':action['app']=self.app.currentText()
        elif kind=='preset':
            if not self.preset.currentData():raise ValueError('Önce pencere düzeni kaydet')
            action['preset']=self.preset.currentData()
        elif kind=='notify':action['text']=self.text.text()
        elif kind=='awake':action['minutes']=self.minutes.value()
        elif kind=='presentation':action['enabled']=True
        elif kind in ('mybrain','photos'):
            if not self.usb.currentData():raise ValueError('Bağlı USB seç')
            action.update({'uuid':self.usb.currentData(),'relative':self.relative.text()})
            if kind=='photos':action['destination']=self.destination.text()
        return {'id':self.original.get('id',str(uuid.uuid4())),'name':self.name.text().strip(),'enabled':self.enabled.isChecked(),'event':event,'value':value,'action':action}

from productivity_ui import ProductivityPages

class Center(ProductivityPages,QMainWindow):
    def __init__(self,page='home'):
        super().__init__();self.setWindowTitle('Violet · Masaüstü');self.resize(1220,820);self.setMinimumSize(860,600);self.jobs=set();self.state={};self.qt={};self.refreshing=False
        root=QWidget();self.setCentralWidget(root);outer=QHBoxLayout(root);outer.setContentsMargins(16,16,16,16);outer.setSpacing(18);self.nav=QListWidget();self.nav.setFixedWidth(205);outer.addWidget(self.nav);self.stack=QStackedWidget();outer.addWidget(self.stack,1)
        self.page_ids=['home','overview','tools','snippets','usb','files','system','rules'];names=['✦  Masaüstü','▦  Pencereler','✎  Ekran / kalem','☷  Metin şablonları','◈  USB cihazlar','↻  Dosyalar','◉  Sistem / ağ','⚙  Kurallar / profiller']
        for label,builder in zip(names,[self.home_page,self.window_page,self.tools_page,self.snippets_page,self.usb_page,self.files_page,self.system_page,self.rules_page]):self.nav.addItem(label);widget=QWidget();layout=QVBoxLayout(widget);layout.setSpacing(12);builder(layout);self.stack.addWidget(widget)
        for page,label in self.extra_pages:
            self.page_ids.append(page);self.nav.addItem(label);widget=QWidget();layout=QVBoxLayout(widget);layout.setSpacing(12);getattr(self,page+'_page')(layout);self.stack.addWidget(widget)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex);self.nav.setCurrentRow(self.page_ids.index(page) if page in self.page_ids else 0)
        self.privacy(bool(read(STATE/'presentation.json',{}).get('enabled')))
        self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(5000);self.refresh();self.reload_config();QShortcut(QKeySequence('Escape'),self,activated=self.close)
    def work(self,fn,done=None,quiet=False,on_error=None):
        job=Job(fn);self.jobs.add(job)
        def finish(value,error):
            self.jobs.discard(job)
            if error:
                if on_error:on_error()
                self.statusBar().showMessage(str(error),10000)
                if not quiet:QMessageBox.warning(self,'İşlem tamamlanamadı',str(error))
            elif done:done(value)
            elif value is not None:self.statusBar().showMessage(str(value),10000)
        job.result.done.connect(finish);QThreadPool.globalInstance().start(job)
    def title(self,layout,text,note=''):
        h=QLabel(text);h.setObjectName('hero');layout.addWidget(h)
        if note:q=QLabel(note);q.setWordWrap(True);layout.addWidget(q)
    def buttons(self,layout,items):
        row=QHBoxLayout();layout.addLayout(row)
        for title,fn in items:
            b=QPushButton(title);b.clicked.connect(lambda _,f=fn:self.guard(f));row.addWidget(b)
        row.addStretch()
    def guard(self,fn):
        try:fn()
        except Exception as e:QMessageBox.warning(self,'Violet',str(e))
    def refresh(self):
        if self.refreshing:return
        self.refreshing=True
        def get():
            suite=request('suite','status')
            try:qt=request('qtile','state')
            except Exception:qt={}
            return suite,qt
        def done(value):self.refreshing=False;self.state,self.qt=value;self.render_state()
        def task():
            try:return get()
            except Exception:self.refreshing=False;raise
        self.work(task,done,True)
    def command(self,action,**args):self.work(lambda:request('suite',action,**args),lambda result:(self.statusBar().showMessage(str(result),10000),self.refresh()))
    def qtcommand(self,action,**args):self.work(lambda:request('qtile',action,**args),lambda result:(self.statusBar().showMessage(str(result),10000),self.refresh()))
    def home_page(self,l):
        self.title(l,'Masaüstün, tek merkezde');l.addWidget(Hero());self.summary=QLabel('Masaüstü servisi bağlanıyor…');self.summary.setWordWrap(True);l.addWidget(self.summary)
        self.buttons(l,[('Pencereler',lambda:self.nav.setCurrentRow(1)),('Ekrana çiz',lambda:spawn(['violet-desktop','annotate'])),('MyBrain',lambda:spawn(APPS['MyBrain']))])
        self.buttons(l,[('Sunum modunu değiştir',lambda:self.command('presentation')),('Düzeni geri al',lambda:self.qtcommand('undo'))])
        awake=QHBoxLayout();l.addLayout(awake);self.minutes=QSpinBox();self.minutes.setRange(1,1440);self.minutes.setValue(30);awake.addWidget(QLabel('Dakika'));awake.addWidget(self.minutes);btn=QPushButton('Uykuyu engelle');btn.clicked.connect(lambda:self.command('awake',minutes=self.minutes.value()));awake.addWidget(btn);btn=QPushButton('İptal');btn.clicked.connect(lambda:self.command('awake',minutes=0));awake.addWidget(btn)
        self.awake_app=QComboBox();l.addWidget(self.awake_app);self.buttons(l,[('Uygulama kapanana dek uyanık',lambda:self.command('awake',app=self.awake_app.currentText())),('Seçili pencerenin uykusunu engelle',self.window_awake)])
        info=QLabel('Sunum modu bildirimleri sessize alır, özel panelleri kapatır ve iki saat uyku engeller. Ekran paylaşımı uygulamandaki pencere/ekran seçimiyle başlar.');info.setWordWrap(True);l.addWidget(info);l.addStretch()
    def window_awake(self,enabled=True):
        ids=self.selected_windows()
        if not ids:raise ValueError('Pencereler bölümünden bir pencere seç')
        self.qtcommand('awake-window',id=ids[0],enabled=enabled)
    def window_page(self,l):
        self.title(l,'Pencere atlası','Ara, seç, çalışma alanına taşı veya bir düzen uygula. Birden fazla kartı Ctrl ile seç.');self.search=QLineEdit();self.search.setPlaceholderText('Pencere adı / uygulama / çalışma alanı');self.search.textChanged.connect(self.render_windows);l.addWidget(self.search)
        self.windows=QListWidget();self.windows.setStyleSheet('QListWidget::item {background:#30263f;border:1px solid #4b3b61;border-radius:12px;margin:5px;padding:12px;} QListWidget::item:selected {background:#55406d;border:1px solid #c5b4ff;}');self.windows.setViewMode(QListView.ViewMode.IconMode);self.windows.setResizeMode(QListView.ResizeMode.Adjust);self.windows.setGridSize(QSize(255,150));self.windows.setIconSize(QSize(48,48));self.windows.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection);self.windows.itemDoubleClicked.connect(lambda item:self.qtcommand('focus',id=item.data(Qt.ItemDataRole.UserRole)));l.addWidget(self.windows,1)
        row=QHBoxLayout();l.addLayout(row);self.group=QComboBox();row.addWidget(self.group);button=QPushButton('Taşı');button.clicked.connect(self.move_windows);row.addWidget(button);self.template=QComboBox()
        for label,template in [('İki sütun','split'),('PDF / not · 63/37','reading'),('Üç sütun','three'),('Sunum','presentation'),('Qtile döşeme','tile')]:self.template.addItem(label,template)
        row.addWidget(self.template);button=QPushButton('Düzeni uygula');button.clicked.connect(self.apply_preset);row.addWidget(button)
        self.buttons(l,[(label,lambda step=step:self.atlas_move(step)) for label,step in [('← Sol',-1),('↑ Yukarı','up'),('↓ Aşağı','down'),('→ Sağ',1)]])
        self.buttons(l,[('Seçili pencereye git',self.focus_window),('Geri al',lambda:self.qtcommand('undo')),('Şablonu kaydet',self.save_preset)])
        self.buttons(l,[('Pencere açıkken uyanık',self.window_awake),('Pencere engelleyicisini kaldır',lambda:self.window_awake(False))])
        self.saved=QComboBox();l.addWidget(self.saved);self.buttons(l,[('Kayıtlı düzeni aç',self.saved_preset),('Kaydı sil',self.delete_preset)])
    def atlas_move(self,step):
        columns=max(1,self.windows.viewport().width()//255)
        offset=-columns if step=='up' else columns if step=='down' else step
        if self.windows.count():self.windows.setCurrentRow(max(0,min(self.windows.count()-1,self.windows.currentRow()+offset)));self.windows.setFocus()
    def selected_windows(self):return [x.data(Qt.ItemDataRole.UserRole) for x in self.windows.selectedItems()]
    def render_windows(self):
        selected=set(self.selected_windows());self.windows.clear();query=self.search.text().casefold()
        for w in self.qt.get('windows',[]):
            label=f'{w.get("name","Uygulama")}\n'+', '.join(w.get('classes',[]))+f'\nAlan {w["group"]}'+(' · Yüzen' if w.get('floating') else '')
            if query and query not in label.casefold():continue
            item=QListWidgetItem(QIcon.fromTheme((w.get('classes') or ['application-x-executable'])[0]),label);item.setData(Qt.ItemDataRole.UserRole,w['id']);item.setToolTip(label);self.windows.addItem(item);item.setSelected(w['id'] in selected)
    def focus_window(self):
        ids=self.selected_windows()
        if not ids:raise ValueError('Önce bir pencere seç')
        self.qtcommand('focus',id=ids[0]);self.close()
    def move_windows(self):
        ids=self.selected_windows();target=self.group.currentText()
        if not ids:raise ValueError('Önce pencereleri seç')
        self.work(lambda:[request('qtile','move',id=i,group=target) for i in ids],lambda _:self.refresh())
    def apply_preset(self):self.qtcommand('preset',ids=self.selected_windows(),group=self.group.currentText(),template=self.template.currentData())
    def save_preset(self):
        ids=self.selected_windows()
        if not ids:raise ValueError('Şablona ait pencereleri seç')
        name,ok=QInputDialog.getText(self,'Düzen kaydet','Ad')
        if not ok or not name.strip():return
        roles=[{'classes':w['classes']} for w in self.qt['windows'] if w['id'] in ids]
        if any(not x['classes'] for x in roles):raise ValueError('Sınıfı olmayan pencere kalıcı şablona eklenemez')
        record={'id':str(uuid.uuid4()),'name':name.strip(),'roles':roles,'template':self.template.currentData(),'group':self.group.currentText()};update(lambda c:c['presets'].append(record));self.reload_config()
    def saved_preset(self):
        p=next((x for x in config()['presets'] if x['id']==self.saved.currentData()),None)
        if not p:raise ValueError('Kayıtlı düzen seç')
        self.qtcommand('saved-preset',**{k:p[k] for k in ('roles','template','group')})
    def delete_preset(self):
        ident=self.saved.currentData()
        if ident and confirm(self,'Bu düzen kaydını sil?'):update(lambda c:c.__setitem__('presets',[p for p in c['presets'] if p['id']!=ident]));self.reload_config()
    def tools_page(self,l):
        self.title(l,'Ekran ve kalem','Alan seç, kalemle çiz, ok ekle veya canlı büyüt. Çizim kaydedilene kadar bellekte kalır.')
        self.buttons(l,[('Ekrana çiz',lambda:spawn(['violet-desktop','annotate'])),('Canlı büyüteç',lambda:spawn(['violet-desktop','magnify'])),('Renk seç',lambda:spawn(['violet-desktop','color']))]);self.palette=table(['HEX','RGB']);l.addWidget(self.palette);self.buttons(l,[('HEX kopyala',self.palette_copy),('Paleti yenile',self.reload_config)]);l.addStretch()
    def palette_copy(self):
        row=self.palette.currentRow();values=config()['palette']
        if 0<=row<len(values):self.copy_text(values[row]['hex'])
    def snippets_page(self,l):
        self.title(l,'Metin şablonları','Tarih ve başlık alanlarını doldur, panoya kopyala, istediğin uygulamaya yapıştır.');self.snippets=QListWidget();self.snippets.currentRowChanged.connect(self.snippet_selected);l.addWidget(self.snippets);self.snippet_name=QLineEdit();self.snippet_name.setPlaceholderText('Şablon adı');l.addWidget(self.snippet_name);self.snippet_text=QTextEdit();self.snippet_text.setPlaceholderText('{date} · {time} · {title}');l.addWidget(self.snippet_text,1);self.buttons(l,[('Yeni',self.new_snippet),('Kaydet',self.save_snippet),('Sil',self.delete_snippet),('Doldur / kopyala',self.expand_snippet)])
    def snippet_selected(self,row):
        values=config()['snippets']
        if 0<=row<len(values):self.snippet_name.setText(values[row]['name']);self.snippet_text.setPlainText(values[row]['text'])
    def new_snippet(self):self.snippets.setCurrentRow(-1);self.snippet_name.clear();self.snippet_text.clear()
    def save_snippet(self):
        name=self.snippet_name.text().strip();text=self.snippet_text.toPlainText();row=self.snippets.currentRow()
        if not name:raise ValueError('Şablon adı gerekli')
        record={'name':name,'text':text};update(lambda c:c['snippets'].__setitem__(row,record) if 0<=row<len(c['snippets']) else c['snippets'].append(record));self.reload_config()
    def delete_snippet(self):
        row=self.snippets.currentRow()
        if row>=0 and confirm(self,'Şablonu sil?'):update(lambda c:c['snippets'].pop(row));self.reload_config()
    def copy_text(self,value):self.work(lambda:subprocess.run(['wl-copy'],input=value.encode(),check=True,timeout=5),lambda _:self.statusBar().showMessage('Panoya kopyalandı',5000))
    def expand_snippet(self):
        text=self.snippet_text.toPlainText();now=dt.datetime.now();text=text.replace('{date}',now.strftime('%Y-%m-%d')).replace('{time}',now.strftime('%H:%M'))
        if '{title}' in text:
            title,ok=QInputDialog.getText(self,'Şablonu doldur','Başlık')
            if not ok:return
            text=text.replace('{title}',title)
        self.copy_text(text)
    def usb_page(self,l):
        self.title(l,'USB cihazları','Açık kasayı kilitle, dosyaları kullanan uygulamaları gör ve cihazı güvenle çıkar.');self.usb=table(['Cihaz','Etiket','Bağlama noktası']);l.addWidget(self.usb,1);self.busy=QTextEdit();self.busy.setReadOnly(True);l.addWidget(self.busy);self.buttons(l,[('Açık dosyaları göster',self.check_busy),('MyBrain kasasını kilitle',lambda:self.work(lambda:request('brain','lock'))),('Güvenle çıkar',self.eject),('USB kuralı ekle',self.add_rule)])
    def usb_selected(self):
        row=self.usb.currentRow();values=self.state.get('mounts',[])
        if not 0<=row<len(values):raise ValueError('USB cihazı seç')
        return values[row]
    def check_busy(self):
        selected=self.usb_selected();points=[p for m in self.state.get('mounts',[]) if m['disk']==selected['disk'] for p in m['mounts']]
        self.work(lambda:users_of(points),lambda value:self.busy.setPlainText(('Bazı işlemlerin dosyaları erişim izni nedeniyle okunamadı.\n' if value['limited'] else '')+'\n'.join(f'{p["pid"]} · {p["name"]}\n'+ '\n'.join(p['files']) for p in value['processes']) or 'Açık dosya bulunamadı; çıkarma sırasında UDisks yeniden denetler.'))
    def eject(self):
        selected=self.usb_selected()
        if confirm(self,f'{selected["label"]} cihazını çıkar? Aynı diskin tüm bağlı bölümleri ayrılır; açık Python MyBrain kasası kilitlenir.'):self.command('eject',device=selected['name'])
    def files_page(self,l):
        self.title(l,'Dosya geçmişi ve senkronizasyon','Seçtiğin klasörlerde değişen dosyaların son 25 sürümü tutulur. Sınır: 32 MiB/dosya, 10.000 dosya/klasör, 1 GiB toplam. Symlink ve geliştirme önbellekleri atlanır.');self.folders=QListWidget();l.addWidget(self.folders);self.buttons(l,[('Klasör ekle',self.add_folder),('Takibi bırak',self.remove_folder),('Şimdi sürüm al',lambda:self.command('history-scan')),('Sürümleri yenile',self.history_refresh)]);self.versions=table(['Dosya','Tarih','Boyut']);l.addWidget(self.versions,1);self.buttons(l,[('Sürümü farklı dosyaya çıkar',self.restore_history),('Syncthing aç',lambda:spawn(APPS['Senkronizasyon'])),('Çakışma dosyalarını bul',self.find_conflicts)]);self.sync=QLabel('Senkronizasyon durumu bekleniyor');self.sync.setWordWrap(True);l.addWidget(self.sync)
    def add_folder(self):
        path=QFileDialog.getExistingDirectory(self,'Sürüm takip klasörü',str(Path.home()))
        if not path:return
        root=Path(path).resolve()
        if root==Path.home().resolve() or root==Path('/'):raise ValueError('Belirli bir belge klasörü seç')
        update(lambda c:c['history'].append(str(root)) if str(root) not in c['history'] else None);self.reload_config();self.command('history-scan')
    def remove_folder(self):
        item=self.folders.currentItem()
        if item:update(lambda c:c['history'].remove(item.text()));self.reload_config()
    def history_refresh(self):
        index=History().manifest();self.history_rows=[]
        for ident,entry in index['files'].items():
            for v in reversed(entry['versions']):self.history_rows.append({'ident':ident,'stamp':v['stamp'],'path':str(Path(index['roots'][entry['root']])/entry['path']),'time':v['time'],'size':v['size']})
        self.history_rows.sort(key=lambda x:x['time'],reverse=True);rows(self.versions,[(x['path'],dt.datetime.fromtimestamp(x['time']).strftime('%d.%m %H:%M:%S'),mb(x['size'])) for x in self.history_rows])
    def restore_history(self):
        i=self.versions.currentRow()
        if not 0<=i<len(self.history_rows):raise ValueError('Önce sürüm seç')
        record=self.history_rows[i];source=Path(record['path']);target,_=QFileDialog.getSaveFileName(self,'Sürümü kopya olarak çıkar',str(source.with_name(source.stem+'-eski'+source.suffix)))
        if target:self.command('history-restore',ident=record['ident'],stamp=record['stamp'],destination=target)
    def find_conflicts(self):
        path=QFileDialog.getExistingDirectory(self,'Syncthing klasörünü seç',str(Path.home()))
        if not path:return
        def scan():
            result=[];count=0
            for current,dirs,files in os.walk(path,followlinks=False):
                dirs[:]=[d for d in dirs if d!='.stversions' and not (Path(current)/d).is_symlink()]
                for name in files:
                    count+=1
                    if count>10000:return result
                    target=Path(current)/name
                    if 'sync-conflict' in name and not target.is_symlink():result.append(str(target))
                    if len(result)>=200:return result
            return result
        self.work(scan,self.show_conflicts)
    def show_conflicts(self,paths):
        dialog=QDialog(self);dialog.setWindowTitle('Senkronizasyon çakışmaları');dialog.resize(800,480);layout=QVBoxLayout(dialog);label=QLabel('İlk 10.000 dosya tarandı; en çok 200 sonuç. Dosyalar korunur; çift tıkla açıp karşılaştır.');label.setWordWrap(True);layout.addWidget(label);files=QListWidget();files.addItems(paths or ['Çakışma dosyası bulunamadı']);layout.addWidget(files)
        if paths:files.itemDoubleClicked.connect(lambda item:spawn(['xdg-open',item.text()]))
        button=QPushButton('Seçili dosyanın klasörünü aç');button.clicked.connect(lambda:spawn(['nautilus',str(Path(files.currentItem().text()).parent)]) if paths and files.currentItem() else None);layout.addWidget(button);dialog.exec()
    def system_page(self,l):
        self.title(l,'Uygulamalar ve ağ','CPU değerleri örnekler arasındaki kullanımdır. Bağlantılar kendi kullanıcı hesabının süreçlerinden okunur.');self.procs=table(['PID','Uygulama','CPU %','Bellek','Durum']);l.addWidget(self.procs,2);self.buttons(l,[('Kapat · SIGTERM',lambda:self.end_process(False)),('Zorla sonlandır',lambda:self.end_process(True)),('Tanı paketi oluştur',self.export_diagnostics)]);self.connections=table(['Uygulama','PID','Uzak bağlantı','Durum']);l.addWidget(self.connections,1);self.network_label=QLabel();self.network_label.setWordWrap(True);l.addWidget(self.network_label);self.buttons(l,[('Uygulama başına canlı trafik',self.nethogs)])
    def end_process(self,kill):
        i=self.procs.currentRow();values=self.state.get('metrics',{}).get('processes',[])
        if not 0<=i<len(values):raise ValueError('Uygulama seç')
        p=values[i]
        if confirm(self,f'{p["name"]} ({p["pid"]}) '+('zorla sonlandırılsın mı? Kaydedilmemiş veriler kaybolabilir.' if kill else 'kapatılsın mı?')):self.command('signal',pid=p['pid'],born=p['born'],kill=kill)
    def export_diagnostics(self):
        path,_=QFileDialog.getSaveFileName(self,'Tanı paketi',str(Path.home()/'violet-tani.zip'),'ZIP (*.zip)')
        if path:self.work(lambda:diagnostics(path),lambda result:QMessageBox.information(self,'Tanı paketi',result+'\nPaylaşmadan önce içeriğini incele. Kullanıcı/system servis hataları ve seçili servis günlükleri içerir.'))
    def nethogs(self):
        QMessageBox.information(self,'Canlı trafik','Terminalde sudo parolanı ister. Nethogs uygulama başına ağ trafiğini gösterir; q ile çıkılır.');spawn(['foot','sudo','nethogs'])
    def rules_page(self,l):
        self.title(l,'Kurallar ve ağ profilleri','USB, uygulama, ağ ve saat olaylarını hazır eylemlere bağla. Kurallar oturum açılışında mevcut USB/uygulamaları yeniden tetiklemez.');self.rules=table(['Ad','Olay','Değer','İşlem','Etkin']);l.addWidget(self.rules,2);self.buttons(l,[('Kural ekle',self.add_rule),('Düzenle',self.edit_rule),('Sil',self.delete_rule),('İşlemi şimdi dene',self.test_rule)]);self.profiles=table(['Ad','Ağ UUID','Düzen','Sunum']);l.addWidget(self.profiles,1);self.buttons(l,[('Bu ağa profil ekle',self.add_profile),('Profili sil',self.delete_profile)])
    def add_rule(self):self.rule_editor(None)
    def edit_rule(self):
        values=config()['rules'];i=self.rules.currentRow()
        if 0<=i<len(values):self.rule_editor(values[i])
    def rule_editor(self,record):
        dlg=RuleDialog(self,self.state,record)
        while dlg.exec()==QDialog.DialogCode.Accepted:
            try:result=dlg.record()
            except ValueError as e:QMessageBox.warning(dlg,'Kural',str(e));continue
            update(lambda c:c.__setitem__('rules',[x for x in c['rules'] if x['id']!=result['id']]+[result]));self.reload_config();break
    def delete_rule(self):
        i=self.rules.currentRow();values=config()['rules']
        if 0<=i<len(values) and confirm(self,'Kuralı sil?'):ident=values[i]['id'];update(lambda c:c.__setitem__('rules',[x for x in c['rules'] if x['id']!=ident]));self.reload_config()
    def test_rule(self):
        i=self.rules.currentRow();values=config()['rules']
        if 0<=i<len(values):self.command('rule-test',ruleAction=values[i]['action'])
    def add_profile(self):
        network=self.state.get('network')
        if not network:raise ValueError('Önce NetworkManager ağına bağlan')
        dialog=QDialog(self);dialog.setWindowTitle('Ağ profili');form=QFormLayout(dialog);name=QLineEdit('Ev');form.addRow('Ad',name);preset=QComboBox();preset.addItem('Düzeni değiştirme','')
        for p in config()['presets']:preset.addItem(p['name'],p['id'])
        form.addRow('Düzen',preset);presentation=QComboBox();presentation.addItem('Sunum modunu değiştirme',None);presentation.addItem('Sunumu aç',True);presentation.addItem('Sunumu kapat',False);form.addRow('Sunum',presentation);buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);form.addRow(buttons)
        if dialog.exec()==QDialog.DialogCode.Accepted:
            value={'id':str(uuid.uuid4()),'name':name.text(),'uuid':network,'preset':preset.currentData(),'presentation':presentation.currentData()};update(lambda c:c.__setitem__('profiles',[p for p in c['profiles'] if p['uuid']!=network]+[value]));self.reload_config()
    def delete_profile(self):
        i=self.profiles.currentRow();values=config()['profiles']
        if 0<=i<len(values):ident=values[i]['id'];update(lambda c:c.__setitem__('profiles',[p for p in c['profiles'] if p['id']!=ident]));self.reload_config()
    def reload_config(self):
        c=config();self.snippets.clear();self.snippets.addItems([x['name'] for x in c['snippets']]);self.folders.clear();self.folders.addItems(c['history']);self.saved.clear()
        for p in c['presets']:self.saved.addItem(p['name'],p['id'])
        rows(self.palette,[(x['hex'],x['rgb']) for x in c['palette']]);rows(self.rules,[(x['name'],x['event'],x['value'],x['action']['kind'],'Evet' if x.get('enabled',True) else 'Hayır') for x in c['rules']]);rows(self.profiles,[(x['name'],x['uuid'],x.get('preset',''),x.get('presentation')) for x in c['profiles']]);self.history_refresh()
    def privacy(self,enabled):
        for i in [j for j in range(len(self.page_ids)) if j not in (0,2,self.page_ids.index('recording'))]:self.nav.setRowHidden(i,enabled)
        if enabled and self.nav.currentRow() not in (0,2,self.page_ids.index('recording')):self.nav.setCurrentRow(0)
    def render_state(self):
        self.privacy(bool(self.state.get('presentation')));self.productivity_state()
        s=self.state;metrics=s.get('metrics',{});awake='Açık' if s.get('awake') else 'Kapalı';self.summary.setText(f'Sunum: {"Açık" if s.get("presentation") else "Kapalı"}    ·    Uykuyu engelle: {awake}\n{len(self.qt.get("windows",[]))} pencere    ·    {len(s.get("mounts",[]))} USB bölüm    ·    {len(config()["rules"])} kural\n'+('\n'.join(x['text'] for x in s.get('errors',[])[-2:])))
        current=self.awake_app.currentText();self.awake_app.clear();self.awake_app.addItems(sorted({p['name'] for p in metrics.get('processes',[])}));self.awake_app.setCurrentText(current)
        current=self.group.currentText();names=[g['name'] for g in self.qt.get('groups',[])];self.group.clear();self.group.addItems(names);self.group.setCurrentText(current if current in names else self.qt.get('current',''))
        self.render_windows();rows(self.usb,[(m['name'],m['label'],' · '.join(m['mounts'])) for m in s.get('mounts',[])]);rows(self.procs,[(p['pid'],p['name'],p['cpu'],mb(p['memory']),p['status']) for p in metrics.get('processes',[])]);rows(self.connections,[(c['name'],c['pid'],c['remote'],c['status']) for c in metrics.get('connections',[])])
        self.network_label.setText('Bu servis oturumundaki toplam: '+' · '.join(f'{n}: ↓ {mb(v["received"])} ↑ {mb(v["sent"])}' for n,v in metrics.get('network',{}).items()))
        sync=s.get('sync',{});self.sync.setText(('Syncthing · '+str(sync.get('devices',0))+' bağlı cihaz\n'+'\n'.join(f'{f["label"]}: {f["state"]} · {f["needFiles"]} dosya bekliyor · {f["errors"]} hata' for f in sync.get('folders',[]))) if sync.get('available') else sync.get('message','Syncthing bağlanıyor'))


def main():
    mode=sys.argv[1] if len(sys.argv)>1 else 'home'
    if mode=='radial':
        try:
            point=request('qtile','pointer');run(['qs','-c','fatih','ipc','call','desktop','pen',str(int(point['x'])),str(int(point['y']))])
        except Exception as e:spawn(['notify-send','Violet',str(e)])
        return
    if mode in ('undo','presentation'):
        try:result=request('qtile' if mode=='undo' else 'suite',mode);spawn(['notify-send','Violet',str(result)])
        except Exception as e:spawn(['notify-send','Violet',str(e)])
        return
    app=QApplication(sys.argv);app.setApplicationName('violet-desktop');app.setStyle('Fusion');app.setStyleSheet(STYLE+Path(__file__).with_name("violet.qss").read_text())
    try:
        if mode in ('annotate','eraser','magnify','color'):
            from screen_tools import Annotation,Magnifier,selected,capture,color_pick
            if mode=='color':spawn(['notify-send','Renk panoya kopyalandı',color_pick()]);return
            region=selected();window=Annotation(capture(region)) if mode in ('annotate','eraser') else Magnifier(region)
            if mode=='eraser':window.tool.setCurrentText('Silgi')
        elif mode in ('palette','drop','quick-note'):
            from interaction import Palette,Drop,QuickNote
            if read(STATE/'presentation.json',{}).get('enabled'):return
            window=Palette() if mode=='palette' else Drop() if mode=='drop' else QuickNote()
        else:window=Center(mode)
        window.show();sys.exit(app.exec())
    except Exception as e:QMessageBox.warning(None,'Violet',str(e))
if __name__=='__main__':main()
