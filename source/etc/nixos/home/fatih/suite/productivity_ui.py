"""Native productivity pages shared by the Violet desktop center."""
import json,os,shlex,subprocess,uuid
from pathlib import Path
from PyQt6.QtCore import Qt,QTimer,QUrl
from PyQt6.QtGui import QIcon,QDesktopServices
from PyQt6.QtWidgets import *
from common import CONFIG,STATE,config,update,request,read
from backend import run,spawn
import productivity as p

def grid(headers):
    t=QTableWidget(0,len(headers));t.setHorizontalHeaderLabels(headers);t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection);t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);t.verticalHeader().hide();return t

def fill(t,values):
    selected=t.currentRow();t.setRowCount(len(values))
    for i,row in enumerate(values):
        for j,v in enumerate(row):t.setItem(i,j,QTableWidgetItem(str(v)))
    if selected<len(values):t.selectRow(selected)

def picked(t,items):
    i=t.currentRow()
    if not 0<=i<len(items):raise ValueError('Önce listeden bir satır seç')
    return items[i]

def edit_json(parent,title,value):
    dialog=QDialog(parent);dialog.setWindowTitle(title);dialog.resize(650,500);l=QVBoxLayout(dialog);l.addWidget(QLabel('Değerleri düzenle; Kaydet mevcut alanları doğrular.'));editor=QPlainTextEdit(json.dumps(value,ensure_ascii=False,indent=2));l.addWidget(editor);b=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);b.accepted.connect(dialog.accept);b.rejected.connect(dialog.reject);l.addWidget(b)
    if dialog.exec():return json.loads(editor.toPlainText())
    return None

class SessionDialog(QDialog):
    def __init__(self,parent,existing=None):
        super().__init__(parent);self.setWindowTitle('Çalışma oturumu');self.resize(850,570);l=QVBoxLayout(self);self.name=QLineEdit((existing or {}).get('name','Hukuk'));l.addWidget(self.name);self.table=QTableWidget(0,3);self.table.setHorizontalHeaderLabels(['Uygulama','Qtile alanı','Mevcut pencereyle eşleşen sınıflar']);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);l.addWidget(self.table);self.entries=p.apps();self.groups=[g['name'] for g in parent.qt.get('groups',[])] or [str(i) for i in range(1,10)];self.ident=(existing or {}).get('id',str(uuid.uuid4()))
        row=QHBoxLayout();l.addLayout(row);add=QPushButton('Uygulama ekle');add.clicked.connect(lambda:self.add());row.addWidget(add);delete=QPushButton('Satırı sil');delete.clicked.connect(lambda:self.table.removeRow(self.table.currentRow()) if self.table.currentRow()>=0 else None);row.addWidget(delete)
        for r in (existing or {}).get('entries',[]):self.add(r)
        b=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);b.accepted.connect(self.accept);b.rejected.connect(self.reject);l.addWidget(b)
    def add(self,row=None):
        i=self.table.rowCount();self.table.insertRow(i);app=QComboBox()
        for a in self.entries:app.addItem(a['name'],a['id'])
        group=QComboBox();group.addItems(self.groups);classes=QLineEdit()
        def changed():
            a=next((a for a in self.entries if a['id']==app.currentData()),None);classes.setText(', '.join(a['classes']) if a else '')
        app.currentIndexChanged.connect(changed);changed()
        if row:app.setCurrentIndex(max(0,app.findData(row['desktop'])));group.setCurrentText(row['group']);classes.setText(', '.join(row['classes']))
        for j,w in enumerate((app,group,classes)):self.table.setCellWidget(i,j,w)
    def value(self):
        out=[]
        for i in range(self.table.rowCount()):
            ident=self.table.cellWidget(i,0).currentData();group=self.table.cellWidget(i,1).currentText();classes=[x.strip() for x in self.table.cellWidget(i,2).text().split(',') if x.strip()]
            if not ident or not classes:raise ValueError('Uygulama ve pencere sınıfı gerekli')
            out.append({'desktop':ident,'group':group,'classes':classes})
        if not self.name.text().strip() or not out:raise ValueError('Oturum adı ve en az bir uygulama gerekli')
        return {'id':self.ident,'name':self.name.text().strip(),'entries':out}

class ProductivityPages:
    extra_pages=[('phone','⌁  Telefon / S24+'),('notifications','♧  Bildirim merkezi'),('sessions','▥  Çalışma oturumları'),('downloads','↓  İndirilenler'),('ocr','⌗  Ekrandan yazı'),('recording','●  Ekran kaydı'),('audio','♫  Uygulama sesleri'),('apps','◇  Uygulamalar'),('storage','◌  Depolama bakımı'),('monitors','▣  Monitörler'),('settings','⚙  Masaüstü ayarları')]
    def phone_page(self,l):
        self.title(l,'S24+ ile masaüstün','Telefonda KDE Connect’i aç, aynı ağa bağlan ve eşleşme isteğini telefonda onayla. Bildirim, pano ve uzaktan giriş izinleri telefon uygulamasından yönetilir.');self.phones=[];self.phone_table=grid(['Cihaz','Erişim','Eşleşme']);l.addWidget(self.phone_table,1)
        self.buttons(l,[('Cihazları bul',self.phone_refresh),('Eşleş',lambda:self.phone_action('pair')),('Telefonum olarak seç',self.phone_save),('Dosya gönder',self.phone_share)])
        self.buttons(l,[('Pano gönder',lambda:self.phone_action('send-clipboard')),('Telefonu çaldır',lambda:self.phone_action('ring')),('Bağlantıyı dene',lambda:self.phone_action('ping')),('KDE Connect ayarları',lambda:spawn(['kdeconnect-app']))])
        note=QLabel('Wayland’da pano paylaşımı için “Pano gönder” düğmesi bulunur. Uzaktan kumanda desteği Qtile / KDE Connect’in mevcut giriş protokolüne bağlıdır; bağlantı testi ve telefon izinleriyle doğrula.');note.setWordWrap(True);l.addWidget(note)
    def phone_refresh(self):
        def done(value):self.phones=value;fill(self.phone_table,[(x['name'],'Bağlı' if x['reachable'] else 'Çevrimdışı','Eşleşti' if x['paired'] else 'Bekliyor') for x in value])
        self.work(p.phones,done)
    def phone_selected(self):return picked(self.phone_table,self.phones)['id']
    def phone_action(self,action):self.work(lambda:p.phone(action,self.phone_selected()))
    def phone_save(self):ident=self.phone_selected();update(lambda c:c.__setitem__('phone',ident));self.statusBar().showMessage('Telefon seçildi',5000)
    def phone_share(self):
        ident=self.phone_selected();paths,_=QFileDialog.getOpenFileNames(self,'Telefona gönder')
        if paths:self.work(lambda:p.phone('share',ident,paths))
    def notifications_page(self,l):
        self.title(l,'Bildirim merkezi','Mako’nun etkin bildirimleri ve oturum içi geçmişi. Yeniden girişte geçmiş temizlenir.');self.notice_items=[];self.notice_filter=QComboBox();self.notice_filter.addItem('Tüm uygulamalar');self.notice_filter.currentTextChanged.connect(self.notice_render);l.addWidget(self.notice_filter);self.notice_search=QLineEdit();self.notice_search.setPlaceholderText('Başlık / metin ara');self.notice_search.textChanged.connect(self.notice_render);l.addWidget(self.notice_search);self.notice_table=grid(['Uygulama','Başlık','Durum']);self.notice_table.itemSelectionChanged.connect(self.notice_show);l.addWidget(self.notice_table,1);self.notice_body=QTextBrowser();self.notice_body.setMaximumHeight(140);l.addWidget(self.notice_body)
        self.buttons(l,[('Yenile',self.notice_refresh),('En son bildirimi geri göster',lambda:self.work(lambda:run(['makoctl','restore']))),('Seçili etkin bildirimi kapat',self.notice_dismiss)])
        row=QHBoxLayout();l.addLayout(row);self.mute_minutes=QSpinBox();self.mute_minutes.setRange(1,1440);self.mute_minutes.setValue(30);row.addWidget(QLabel('Dakika'));row.addWidget(self.mute_minutes);mute=QPushButton('Sessize al');mute.clicked.connect(lambda:self.command('mute',minutes=self.mute_minutes.value()));row.addWidget(mute);cancel=QPushButton('Sessizi kaldır');cancel.clicked.connect(lambda:self.command('mute',minutes=0));row.addWidget(cancel)
    def notice_refresh(self):
        def done(value):
            self.notice_items=value;selected=self.notice_filter.currentText();self.notice_filter.blockSignals(True);self.notice_filter.clear();self.notice_filter.addItems(['Tüm uygulamalar']+sorted({x.get('app_name') or 'Uygulama' for x in value}));self.notice_filter.setCurrentText(selected if self.notice_filter.findText(selected)>=0 else 'Tüm uygulamalar');self.notice_filter.blockSignals(False);self.notice_render()
        self.work(p.notifications,done)
    def notice_render(self,*_):
        query=self.notice_search.text().casefold();app=self.notice_filter.currentText();self.visible_notices=[x for x in self.notice_items if (app=='Tüm uygulamalar' or app==(x.get('app_name') or 'Uygulama')) and query in ((x.get('summary') or '')+' '+(x.get('body') or '')).casefold()];fill(self.notice_table,[(x.get('app_name'),x.get('summary'),'Geçmiş' if x['history'] else 'Etkin') for x in self.visible_notices])
    def notice_show(self):
        try:x=picked(self.notice_table,getattr(self,'visible_notices',[]));self.notice_body.setPlainText((x.get('summary') or '')+'\n\n'+(x.get('body') or ''))
        except ValueError:self.notice_body.clear()
    def notice_dismiss(self):
        x=picked(self.notice_table,self.visible_notices)
        if x['history']:raise ValueError('Seçili bildirim zaten geçmişte')
        self.work(lambda:run(['makoctl','dismiss','-n',str(int(x['id']))]),lambda _:self.notice_refresh())
    def sessions_page(self,l):
        self.title(l,'Çalıştığın yere geri dön','Hukuk, Kod veya Okuma: uygulamaları seç, çalışma alanlarını belirle. Açık uygulamalar yeniden kullanılabilir; yeni pencereler kayıtlı sınıflara göre yerleştirilir.');self.session_table=grid(['Oturum','Uygulama / alan']);l.addWidget(self.session_table,1);self.buttons(l,[('Yeni oturum',self.session_add),('Düzenle',lambda:self.session_add(True)),('Aç',self.session_open),('Sil',lambda:self.remove_record('sessions',self.session_selected()['id'],self.session_reload))]);self.session_reload()
    def session_reload(self):self.sessions=config()['sessions'];fill(self.session_table,[(s['name'],', '.join(e['desktop']+' → '+e['group'] for e in s['entries'])) for s in self.sessions])
    def session_selected(self):return picked(self.session_table,self.sessions)
    def session_add(self,edit=False):
        dialog=SessionDialog(self,self.session_selected() if edit else None)
        if dialog.exec():
            value=dialog.value();update(lambda c:c.__setitem__('sessions',[x for x in c['sessions'] if x['id']!=value['id']]+[value]));self.session_reload()
    def session_open(self):
        session=self.session_selected();entries=p.apps();resolved=[]
        for item in session['entries']:
            app=next((a for a in entries if a['id']==item['desktop']),None) or next((a for a in entries if set(a['classes']) & set(item['classes'])),None)
            if not app:raise ValueError('Uygulama kaydı kaldırılmış: '+item['desktop'])
            resolved.append({**item,'argv':app['argv']})
        self.qtcommand('session',entries=resolved)
    def remove_record(self,key,ident,done):
        if QMessageBox.question(self,'Violet','Seçili kaydı sil?')==QMessageBox.StandardButton.Yes:update(lambda c:c.__setitem__(key,[x for x in c[key] if x['id']!=ident]));done()
    def downloads_page(self,l):
        self.title(l,'İndirilenler, düzenli','Tamamlanmış ve en az 30 saniye değişmemiş dosyaları işler. Mevcut dosyanın üzerine yazmaz. Önizleme → Uygula → gerekirse Geri al.');row=QHBoxLayout();l.addLayout(row);self.download_root=QLineEdit(config()['downloadRoot']);row.addWidget(self.download_root);b=QPushButton('Klasör');b.clicked.connect(lambda:self.choose_folder(self.download_root));row.addWidget(b);self.download_table=grid(['Kaynak','Hedef']);l.addWidget(self.download_table,1);self.file_plan=[]
        self.buttons(l,[('Türlere göre önizle',lambda:self.download_preview()),('Uygula',self.download_apply),('Son taşımayı geri al',lambda:self.work(p.undo_downloads)),('Kuralları düzenle',self.download_rules)])
        self.rename_pattern=QLineEdit('{name}-{n:03}{ext}');l.addWidget(self.rename_pattern);self.buttons(l,[('Toplu adlandırmayı önizle',lambda:self.download_preview(self.rename_pattern.text()))]);self.download_auto=QCheckBox('Bu klasörde türlere göre otomatik ayır (her 60 saniye)');self.download_auto.setChecked(config()['downloadAuto']);l.addWidget(self.download_auto);self.buttons(l,[('Klasör / otomasyonu kaydet',self.download_save)])
    def choose_folder(self,entry):
        path=QFileDialog.getExistingDirectory(self,'Klasör seç',entry.text())
        if path:entry.setText(path)
    def download_preview(self,pattern=None):
        root=self.download_root.text()
        def done(value):self.file_plan=value;fill(self.download_table,[(x['source'],x['target']) for x in value]);self.statusBar().showMessage(f'{len(value)} dosya için önizleme',5000)
        self.work(lambda:p.download_plan(root,pattern=pattern),done)
    def download_apply(self):
        if self.file_plan and QMessageBox.question(self,'Dosyaları düzenle',f'{len(self.file_plan)} dosyanın yerini/adını değiştirmek istiyor musun?')==QMessageBox.StandardButton.Yes:
            plan=list(self.file_plan);self.work(lambda:p.apply_plan(plan),lambda result:(self.statusBar().showMessage(result,10000),self.download_preview()))
    def download_save(self):
        root=Path(self.download_root.text()).expanduser().resolve()
        if not root.is_dir():raise ValueError('Klasör bulunamadı')
        update(lambda c:c.update(downloadRoot=str(root),downloadAuto=self.download_auto.isChecked()));self.statusBar().showMessage('İndirilenler ayarı kaydedildi',5000)
    def download_rules(self):
        dialog=QDialog(self);dialog.setWindowTitle('İndirilenler kuralları');dialog.resize(630,420);l=QVBoxLayout(dialog);l.addWidget(QLabel('Uzantıları virgülle yaz. Hedef, seçili klasörün içindeki alt klasördür.'));t=QTableWidget(0,2);t.setHorizontalHeaderLabels(['Uzantılar','Alt klasör']);t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);l.addWidget(t)
        for i,r in enumerate(config()['downloadRules']):t.insertRow(i);t.setItem(i,0,QTableWidgetItem(', '.join(r['extensions'])));t.setItem(i,1,QTableWidgetItem(r['folder']))
        b=QPushButton('Satır ekle');b.clicked.connect(lambda:t.insertRow(t.rowCount()));l.addWidget(b);buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);l.addWidget(buttons)
        if dialog.exec():
            rules=[]
            for i in range(t.rowCount()):
                ext=t.item(i,0);folder=t.item(i,1)
                if not ext or not ext.text().strip():continue
                if not folder or not folder.text().strip():raise ValueError('Alt klasör gerekli')
                name=Path(folder.text().strip())
                if name.is_absolute() or '..' in name.parts:raise ValueError('Alt klasör dışarı çıkamaz')
                rules.append({'extensions':[x.strip().lower().lstrip('.') for x in ext.text().split(',') if x.strip()],'folder':str(name)})
            update(lambda c:c.__setitem__('downloadRules',rules))
    def ocr_page(self,l):
        self.title(l,'Ekrandaki yazıyı al','Alanı seç, Türkçe / İngilizce metni gözden geçir; panoya, çeviriye veya açık MyBrain kasana gönder.');self.ocr_language=QComboBox();self.ocr_language.addItems(['tur+eng','tur','eng']);l.addWidget(self.ocr_language);self.ocr_text=QTextEdit();l.addWidget(self.ocr_text,1);self.buttons(l,[('Alan seç / yazıyı çıkar',self.ocr_capture),('Kopyala',lambda:self.copy_text(self.ocr_text.toPlainText())),('Çeviride aç',self.ocr_translate),('MyBrain’e not',self.ocr_brain)])
    def ocr_capture(self):
        self.hide();language=self.ocr_language.currentText()
        def task():region=run(['slurp']).strip();return p.ocr(region,language)
        def done(value):self.show();self.ocr_text.setPlainText(value)
        QTimer.singleShot(180,lambda:self.work(task,done,on_error=self.show))
    def ocr_translate(self):
        from urllib.parse import urlencode
        text=self.ocr_text.toPlainText()
        if not text:raise ValueError('Önce metin çıkar')
        if QMessageBox.question(self,'Çeviriye gönder','Seçili metni Google Translate web sayfasına gönder?')==QMessageBox.StandardButton.Yes:QDesktopServices.openUrl(QUrl('https://translate.google.com/?'+urlencode({'sl':'auto','tl':'tr','text':text,'op':'translate'})))
    def ocr_brain(self):text=self.ocr_text.toPlainText();self.work(lambda:request('brain','quick-note',title='Ekrandan yazı',body=text))
    def recording_page(self,l):
        self.title(l,'Ekran kaydı ve tekrar','Tam ekran, seçili alan veya pencerenin bulunduğu dikdörtgeni kaydet. Tekrar tamponu son 30/60 saniyeyi saklar; en son açık 0–5 saniyelik parça sonraki kayda girer.');self.record_status=QLabel('Kayıt kapalı');l.addWidget(self.record_status);self.record_region=QLineEdit();self.record_region.setPlaceholderText('Boş: tüm ekranlar · örnek: 0,0 1920x1080');l.addWidget(self.record_region);self.buttons(l,[('Alan seç',self.record_choose),('Pencere seç',self.record_window),('Tam ekran',self.record_region.clear)])
        self.record_audio=QComboBox();self.record_audio.setEditable(True);self.record_audio.addItem('Sessiz','');l.addWidget(QLabel('Ses kaynağı (monitör kaynağı masaüstü sesini kaydeder)'));l.addWidget(self.record_audio);self.buttons(l,[('Ses kaynaklarını yenile',self.record_sources),('Kayıt başlat',self.record_start),('Durdur / kaydet',lambda:self.command('record-stop')),('Tekrar tamponunu başlat',lambda:self.command('record-start',kind='replay',region=self.record_region.text(),audio_source=self.record_audio.currentData() or ''))]);self.buttons(l,[('Son 30 saniyeyi kaydet',lambda:self.record_export(30)),('Son 60 saniyeyi kaydet',lambda:self.record_export(60))]);l.addStretch()
    def record_choose(self):
        self.hide()
        def done(value):self.record_region.setText(value.strip());self.show()
        QTimer.singleShot(180,lambda:self.work(lambda:run(['slurp']),done,on_error=self.show))
    def record_window(self):
        wins=self.qt.get('windows',[]);labels=[w.get('name','Pencere')+' · '+str(w['id']) for w in wins];label,ok=QInputDialog.getItem(self,'Pencere kaydı','Pencere',labels,0,False)
        if ok:
            w=wins[labels.index(label)];self.record_region.setText(f"{w.get('x',0)},{w.get('y',0)} {w.get('width',640)}x{w.get('height',480)}")
    def record_sources(self):
        def done(value):
            self.record_audio.clear();self.record_audio.addItem('Sessiz','')
            for x in value:self.record_audio.addItem(x.get('description',x['name']),x['name'])
        self.work(lambda:json.loads(run(['pactl','-f','json','list','sources'])),done)
    def new_record_path(self):return QFileDialog.getSaveFileName(self,'Kaydı kaydet',str(Path.home()/'Videos/kayit.mkv'),'Matroska (*.mkv)')[0]
    def record_start(self):
        target=self.new_record_path()
        if target:self.command('record-start',kind='record',target=target,region=self.record_region.text(),audio_source=self.record_audio.currentData() or '')
    def record_export(self,seconds):
        target=self.new_record_path()
        if target:self.work(lambda:request('suite','record-export',_timeout=75,seconds=seconds,target=target))
    def audio_page(self,l):
        self.title(l,'Her uygulamanın sesi','Firefox, mpv ve diğer çalışan ses akışlarını ayrı ayarla veya farklı çıkışa taşı.');self.audio_items=[];self.audio_table=grid(['Uygulama','Medya','Ses','Çıkış']);self.audio_table.itemSelectionChanged.connect(self.audio_selected);l.addWidget(self.audio_table,1);row=QHBoxLayout();l.addLayout(row);self.stream_volume=QSpinBox();self.stream_volume.setRange(0,150);self.stream_volume.setSuffix('%');row.addWidget(self.stream_volume);self.stream_mute=QCheckBox('Sessiz');row.addWidget(self.stream_mute);self.stream_sink=QComboBox();row.addWidget(self.stream_sink,1);self.buttons(l,[('Yenile',self.audio_refresh),('Seçili akışa uygula',self.audio_apply),('Gelişmiş ses ayarları',lambda:spawn(['pavucontrol']))])
    def audio_refresh(self):
        def done(value):
            self.audio_items=value['streams'];self.stream_sink.clear()
            for s in value['sinks']:self.stream_sink.addItem(s.get('description',s['name']),s['name'])
            self.sink_names={s['index']:s.get('description',s['name']) for s in value['sinks']};fill(self.audio_table,[(x.get('properties',{}).get('application.name','Uygulama'),x.get('properties',{}).get('media.name',''),self.audio_volume(x),self.sink_names.get(x.get('sink'),x.get('sink'))) for x in self.audio_items])
        self.work(p.audio,done)
    def audio_volume(self,x):
        values=list(x.get('volume',{}).values());return values[0].get('value_percent','0%') if values else '0%'
    def audio_selected(self):
        try:x=picked(self.audio_table,self.audio_items);self.stream_volume.setValue(int(float(self.audio_volume(x).rstrip('%'))));self.stream_mute.setChecked(x.get('mute',False))
        except (ValueError,TypeError):pass
    def audio_apply(self):
        x=picked(self.audio_table,self.audio_items);volume=self.stream_volume.value();sink=self.stream_sink.currentData();mute=self.stream_mute.isChecked();self.work(lambda:p.audio_set(x['index'],volume,sink,mute),lambda _:self.audio_refresh())
    def apps_page(self,l):
        self.title(l,'Uygulamalar, bir yerde','Sistem Nix uygulamalarını görüntüle; kullanıcı Nix profili, kullanıcı Flatpak ve içe aktarılan AppImage paketlerini yönet.');self.app_items=[];self.app_filter=QLineEdit();self.app_filter.setPlaceholderText('Uygulama ara');self.app_filter.textChanged.connect(self.apps_render);l.addWidget(self.app_filter);self.app_table=grid(['Uygulama','Kaynak','Kimlik']);l.addWidget(self.app_table,1);self.buttons(l,[('Yenile',self.apps_refresh),('Aç',self.app_open),('Kullanıcı paketini kaldır',self.app_remove),('AppImage ekle',lambda:spawn(['violet-appimage'])),('Flatseal',lambda:spawn(['flatseal']))]);row=QHBoxLayout();l.addLayout(row);self.install_kind=QComboBox();self.install_kind.addItems(['flatpak','nix']);row.addWidget(self.install_kind);self.install_id=QLineEdit();self.install_id.setPlaceholderText('org.example.App / nixpkgs paket adı');row.addWidget(self.install_id,1);b=QPushButton('Kullanıcıya kur');b.clicked.connect(lambda:self.guard(lambda:self.work(lambda:p.app_manage(self.install_kind.currentText(),'install',self.install_id.text().strip()))));row.addWidget(b)
    def apps_refresh(self):
        def done(value):
            self.app_items=[{'kind':'desktop','id':a['id'],'name':a['name'],'source':a['source']} for a in value['desktop']]+[{'kind':kind,'id':a['id'],'name':a['name'],'source':kind+(' / '+a.get('installation','') if kind=='flatpak' else '')} for kind in ('flatpak','nix','appimage') for a in value[kind]];self.apps_render();self.statusBar().showMessage(' · '.join(value['errors']),10000)
        self.work(p.inventory,done)
    def apps_render(self):self.visible_apps=[x for x in self.app_items if self.app_filter.text().casefold() in (x['name']+' '+x['id']).casefold()];fill(self.app_table,[(x['name'],x['source'],x['id']) for x in self.visible_apps])
    def app_open(self):
        a=picked(self.app_table,self.visible_apps)
        if a['kind']=='desktop':self.work(lambda:p.launch(a['id']))
        elif a['kind']=='flatpak':spawn(['flatpak','run',a['id']])
        elif a['kind']=='appimage':spawn(['appimage-run',a['id']])
        else:raise ValueError('Bu Nix paketini masaüstü uygulama satırından aç')
    def app_remove(self):
        a=picked(self.app_table,self.visible_apps)
        if a['kind']=='desktop':raise ValueError('Sistem Nix paketleri NixOS yapılandırmasından yönetilir')
        if QMessageBox.question(self,'Paketi kaldır',a['name']+' kaldırılsın mı?')==QMessageBox.StandardButton.Yes:self.work(lambda:p.app_manage(a['kind'],'remove',a['id']),lambda result:self.statusBar().showMessage(result,10000))
    def storage_page(self,l):
        self.title(l,'Depolama bakımı','Seçili klasörde en çok 60.000 dosyayı tarar. Yinelenenler boyut + SHA-256 ile karşılaştırılır; benzer fotoğraflar için Czkawka’yı aç.');row=QHBoxLayout();l.addLayout(row);self.storage_root=QLineEdit(str(Path.home()));row.addWidget(self.storage_root);b=QPushButton('Klasör');b.clicked.connect(lambda:self.choose_folder(self.storage_root));row.addWidget(b);self.storage_items=[];self.storage_table=grid(['Dosya','MiB','Tür']);l.addWidget(self.storage_table,1);self.buttons(l,[('Tara',self.storage_scan),('Seçili dosyayı aç',lambda:spawn(['xdg-open',picked(self.storage_table,self.storage_items)['path']])),('Seçileni çöp kutusuna taşı',self.storage_trash),('Czkawka / benzer fotoğraflar',lambda:spawn(['czkawka_gui']))]);self.generations=QPlainTextEdit();self.generations.setReadOnly(True);self.generations.setMaximumHeight(120);l.addWidget(self.generations);self.buttons(l,[('Nix nesillerini göster',lambda:self.work(p.generations,self.generations.setPlainText)),('Eski sistem neslini kaldır',self.generation_remove),('Kullanıcı Nix çöpünü temizle',self.user_gc)])
    def storage_scan(self):
        root=self.storage_root.text()
        def done(v):
            duplicate={path for group in v['duplicates'] for path in group['paths']};self.storage_items=v['large'];fill(self.storage_table,[(x['path'],f"{x['size']/1024/1024:.1f}",'Yinelenen' if x['path'] in duplicate else 'Dosya') for x in v['large']]);self.statusBar().showMessage(f"{v['count']} dosya · {len(v['duplicates'])} yinelenen küme · en büyük 300 dosya",10000)
            # Full duplicate groups are selectable, including duplicates outside the largest 300.
            for group in v['duplicates']:
                for path in group['paths']:
                    if path not in {x['path'] for x in self.storage_items}:self.storage_items.append({'path':path,'size':group['size']})
            fill(self.storage_table,[(x['path'],f"{x['size']/1024/1024:.1f}",'Yinelenen' if x['path'] in duplicate else 'Dosya') for x in self.storage_items])
        self.work(lambda:p.storage(root),done)
    def storage_trash(self):
        item=picked(self.storage_table,self.storage_items);path=item['path']
        if QMessageBox.question(self,'Çöp kutusu',path+' çöp kutusuna taşınsın mı?')==QMessageBox.StandardButton.Yes:self.work(lambda:run(['gio','trash',str(p.regular(path))]),lambda _:self.storage_scan())
    def generation_remove(self):
        listing=p.generations();choices=[line.split()[0] for line in listing.splitlines() if line.split() and line.split()[0].isdigit() and '(current)' not in line];value,ok=QInputDialog.getItem(self,'Eski Nix nesli','Silinecek eski nesil',choices,0,False)
        if ok and value and QMessageBox.question(self,'Nix nesli',f'Eski sistem nesli {value} kaldırılacak. Yetki terminalde istenecek. Devam?')==QMessageBox.StandardButton.Yes:spawn(['foot','-e','sudo','nix-env','-p','/nix/var/nix/profiles/system','--delete-generations',value])
    def user_gc(self):
        if QMessageBox.question(self,'Kullanıcı Nix çöpü','Kullanıcı profilinin referans vermediği Nix nesnelerini temizle?')==QMessageBox.StandardButton.Yes:spawn(['foot','-e','nix','store','gc'])
    def monitors_page(self,l):
        self.title(l,'Monitör profilleri','Bağlı ekranların çözünürlük, ölçek, konum ve dönüşünü kaydet. Otomatik profil yalnız aynı ekran isimleri bağlandığında uygulanır.');self.monitor_table=QTableWidget(0,7);self.monitor_table.setHorizontalHeaderLabels(['Çıkış','Açık','Çözünürlük @ Hz','Ölçek','X','Y','Dönüş']);self.monitor_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);l.addWidget(self.monitor_table,1);self.monitor_name=QLineEdit('Masa');l.addWidget(self.monitor_name);self.monitor_auto=QCheckBox('Bu profil ekran bağlantısı değişince otomatik uygulansın');l.addWidget(self.monitor_auto);self.monitor_groups=QLineEdit();self.monitor_groups.setPlaceholderText('Ekran sırasına göre Qtile alanları: 1, 2 (boş: koru)');l.addWidget(self.monitor_groups);self.buttons(l,[('Bağlı ekranları oku',self.monitor_refresh),('Tablodaki düzeni uygula',self.monitor_apply),('Profil kaydet',self.monitor_save)]);self.monitor_saved=QComboBox();l.addWidget(self.monitor_saved);self.buttons(l,[('Profili tabloya yükle',self.monitor_load),('Seçili profili sil',self.monitor_delete)]);self.monitor_profiles_reload()
    def monitor_refresh(self):self.work(lambda:p.monitor_rows(p.outputs()),self.monitor_fill)
    def monitor_fill(self,rows):
        self.monitor_table.setRowCount(len(rows))
        for i,row in enumerate(rows):
            for j,key in enumerate(('name','enabled','mode','scale','x','y','transform')):
                item=QTableWidgetItem(str(row[key]));self.monitor_table.setItem(i,j,item)
                if j==0:item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    def monitor_values(self):
        rows=[]
        for i in range(self.monitor_table.rowCount()):
            vals=[self.monitor_table.item(i,j).text() for j in range(7)];rows.append(dict(name=vals[0],enabled=vals[1].lower() in ('true','1','evet'),mode=vals[2],scale=float(vals[3]),x=int(vals[4]),y=int(vals[5]),transform=vals[6]))
        return rows
    def monitor_apply(self):
        rows=self.monitor_values();groups=[x.strip() for x in self.monitor_groups.text().split(',') if x.strip()];self.work(lambda:p.apply_monitors(rows,groups))
    def monitor_save(self):
        rows=self.monitor_values();p.monitor_args(rows,p.monitor_rows(p.outputs()));name=self.monitor_name.text().strip()
        if not name:raise ValueError('Profil adı gerekli')
        value={'id':str(uuid.uuid4()),'name':name,'rows':rows,'auto':self.monitor_auto.isChecked(),'groups':[x.strip() for x in self.monitor_groups.text().split(',') if x.strip()]};update(lambda c:c['monitorProfiles'].append(value));self.monitor_profiles_reload()
    def monitor_profiles_reload(self):self.monitor_saved.clear();[self.monitor_saved.addItem(p['name'],p['id']) for p in config()['monitorProfiles']]
    def monitor_load(self):
        value=next((x for x in config()['monitorProfiles'] if x['id']==self.monitor_saved.currentData()),None)
        if not value:raise ValueError('Profil seç')
        self.monitor_name.setText(value['name']);self.monitor_auto.setChecked(value['auto']);self.monitor_groups.setText(', '.join(value['groups']));self.monitor_fill(value['rows'])
    def monitor_delete(self):self.remove_record('monitorProfiles',self.monitor_saved.currentData(),self.monitor_profiles_reload)
    def settings_page(self,l):
        self.title(l,'Masaüstünü kendine göre ayarla','Kısayollar, dock, panel sırası ve hareket hızı. Değişiklikler bu oturumda uygulanır ve yeniden girişte korunur.');tabs=QTabWidget();l.addWidget(tabs,1)
        keys=QWidget();kl=QVBoxLayout(keys);tabs.addTab(keys,'Kısayollar');self.shortcut_table=QTableWidget(0,3);self.shortcut_table.setHorizontalHeaderLabels(['İşlem','Değiştiriciler','Tuş']);self.shortcut_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);kl.addWidget(self.shortcut_table);self.buttons(kl,[('Kısayolları kaydet',self.shortcuts_save),('Varsayılanlara dön',self.shortcuts_reset)])
        self.shortcut_actions={'home':('space','Merkez'),'overview':('w','Pencereler'),'undo':('z','Düzeni geri al'),'annotate':('a','Ekrana çiz'),'magnify':('g','Büyüteç'),'color':('c','Renk seç'),'snippets':('t','Metin şablonları'),'presentation':('F9','Sunum'),'palette':('p','Komut paleti'),'radial':('r','Kalem halkası'),'drop':('f','Dosya işlem alanı'),'ocr':('x','Ekrandan yazı'),'recording':('v','Ekran kaydı')};self.shortcuts_fill()
        dock=QWidget();dl=QVBoxLayout(dock);tabs.addTab(dock,'Dock');self.dock_list=QListWidget();self.dock_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove);dl.addWidget(self.dock_list);self.buttons(dl,[('Uygulama sabitle',self.dock_add),('Seçiliyi kaldır',lambda:self.dock_list.takeItem(self.dock_list.currentRow())),('Sırayı kaydet',self.dock_save),('Varsayılan dock',self.dock_reset)]);self.dock_fill()
        panel=QWidget();pl=QVBoxLayout(panel);tabs.addTab(panel,'Panel / hareket');pl.addWidget(QLabel('Üstbar araçlarını sürükleyerek sırala.'));self.panel_list=QListWidget();self.panel_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove);self.panel_list.addItems(config()['panelOrder']);pl.addWidget(self.panel_list);self.motion=QDoubleSpinBox();self.motion.setRange(.5,1.5);self.motion.setSingleStep(.1);self.motion.setValue(config()['motionSpeed'] or 1);pl.addWidget(QLabel('Animasyon süresi çarpanı (0,5 hızlı · 1,5 sakin)'));pl.addWidget(self.motion);self.pen_button=QComboBox();self.pen_button.addItem('Kalem düğmelerini uygulamalara bırak',0);self.pen_button.addItem('Birinci yan düğme → halka menü',331);self.pen_button.addItem('İkinci yan düğme → halka menü',332);self.pen_button.setCurrentIndex(max(0,self.pen_button.findData(config()['penButton'])));pl.addWidget(self.pen_button);self.pen_secondary=QComboBox()
        for label,action in [('Silgi / ekran çizimi','eraser'),('Ekrana çiz','annotate'),('Hızlı not','quick-note'),('Komut paleti','palette'),('MyBrain','mybrain'),('Uygulamaya bırak','none')]:self.pen_secondary.addItem(label,action)
        self.pen_secondary.setCurrentIndex(max(0,self.pen_secondary.findData(config().get('penSecondary','eraser'))));pl.addWidget(QLabel('Diğer kalem tuşu'));pl.addWidget(self.pen_secondary);self.buttons(pl,[('Panel / hareket / kalem kaydet',self.panel_save),('Halka menüyü aç',lambda:spawn(['violet-desktop','radial'])),('Mevcut tema ayarları',lambda:spawn(['qs','-c','fatih','ipc','call','desktop','settings']))])
        search=QWidget();sl=QVBoxLayout(search);tabs.addTab(search,'Arama / komutlar');self.search_roots=QListWidget();self.search_roots.addItems(config()['searchRoots']);sl.addWidget(QLabel('Komut paletinde dosya aranacak klasörler'));sl.addWidget(self.search_roots);self.buttons(sl,[('Klasör ekle',self.search_root_add),('Seçili klasörü çıkar',self.search_root_remove)]);self.commands_list=QListWidget();sl.addWidget(self.commands_list);self.command_reload();self.buttons(sl,[('Komut ekle',self.command_add),('Komut sil',self.command_remove),('Komut paletini aç',lambda:spawn(['violet-desktop','palette']))])
    def shortcuts_fill(self):
        self.shortcut_table.setRowCount(len(self.shortcut_actions));settings=config()['shortcuts']
        for i,(action,(key,label)) in enumerate(self.shortcut_actions.items()):
            value=settings.get(action,{'mods':['mod4','mod1'],'key':key});item=QTableWidgetItem(label);item.setData(Qt.ItemDataRole.UserRole,action);item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable);self.shortcut_table.setItem(i,0,item);self.shortcut_table.setItem(i,1,QTableWidgetItem(', '.join(value['mods'])));self.shortcut_table.setItem(i,2,QTableWidgetItem(value['key']))
    def shortcuts_save(self):
        values={}
        for i in range(self.shortcut_table.rowCount()):values[self.shortcut_table.item(i,0).data(Qt.ItemDataRole.UserRole)]={'mods':[x.strip().lower() for x in self.shortcut_table.item(i,1).text().split(',') if x.strip()],'key':self.shortcut_table.item(i,2).text().strip()}
        self.work(lambda:request('qtile','shortcuts',bindings=values),lambda result:(update(lambda c:c.__setitem__('shortcuts',values)),self.statusBar().showMessage(result,10000)))
    def shortcuts_reset(self):self.work(lambda:request('qtile','shortcuts',bindings={}),lambda _:(update(lambda c:c.__setitem__('shortcuts',{})),self.shortcuts_fill()))
    def default_pins(self):return [{'name':'MyBrain','icon':'slate','aliases':['mybrain-python'],'command':['mybrain-python']},{'name':'Firefox','icon':'compass','aliases':['firefox','org.mozilla.firefox'],'command':['firefox']},{'name':'Terminal','icon':'terminal','aliases':['foot','footclient'],'command':['kitty']},{'name':'Dosyalar','icon':'folder','aliases':['org.gnome.nautilus','nautilus'],'command':['nautilus']}]
    def dock_fill(self):
        self.dock_list.clear()
        for pin in config()['dockPins'] if config()['dockPins'] is not None else self.default_pins():item=QListWidgetItem(pin['name']);item.setData(Qt.ItemDataRole.UserRole,pin);self.dock_list.addItem(item)
    def dock_add(self):
        entries=p.apps();labels=[a['name']+' · '+a['id'] for a in entries];label,ok=QInputDialog.getItem(self,'Dock','Uygulama',labels,0,False)
        if ok:
            a=entries[labels.index(label)];pin={'name':a['name'],'icon':'rune','iconSource':a['icon'],'aliases':[x.lower() for x in a['classes']],'command':a['argv']};item=QListWidgetItem(pin['name']);item.setData(Qt.ItemDataRole.UserRole,pin);self.dock_list.addItem(item)
    def dock_save(self):
        if self.dock_list.count()>12:raise ValueError('Dock’a en çok 12 uygulama sabitle')
        pins=[self.dock_list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.dock_list.count())];update(lambda c:c.__setitem__('dockPins',pins))
    def dock_reset(self):update(lambda c:c.__setitem__('dockPins',None));self.dock_fill()
    def panel_save(self):
        order=[self.panel_list.item(i).text() for i in range(self.panel_list.count())];speed=self.motion.value();button=self.pen_button.currentData();update(lambda c:c.update(panelOrder=order,motionSpeed=speed,penButton=button,penSecondary=self.pen_secondary.currentData()));self.statusBar().showMessage('Panel / hareket / kalem ayarları kaydedildi',10000)
    def search_root_add(self):
        path=QFileDialog.getExistingDirectory(self,'Arama klasörü')
        if path:update(lambda c:c.__setitem__('searchRoots',list(dict.fromkeys(c['searchRoots']+[path]))));self.search_roots.clear();self.search_roots.addItems(config()['searchRoots'])
    def search_root_remove(self):
        item=self.search_roots.currentItem()
        if item:update(lambda c:c.__setitem__('searchRoots',[p for p in c['searchRoots'] if p!=item.text()]));self.search_roots.clear();self.search_roots.addItems(config()['searchRoots'])
    def command_reload(self):self.commands_list.clear();[self.commands_list.addItem(c['name']) for c in config()['commands']]
    def command_add(self):
        name,ok=QInputDialog.getText(self,'Kayıtlı komut','Ad')
        if not ok or not name.strip():return
        text,ok=QInputDialog.getText(self,'Kayıtlı komut','Program ve argümanlar (örnek: foot -e htop)')
        if ok:argv=p.valid_argv(shlex.split(text));update(lambda c:c['commands'].append({'id':str(uuid.uuid4()),'name':name.strip(),'argv':argv}));self.command_reload()
    def command_remove(self):
        values=config()['commands'];i=self.commands_list.currentRow()
        if 0<=i<len(values):self.remove_record('commands',values[i]['id'],self.command_reload)
    def productivity_state(self):
        recorder=self.state.get('recorder',{});mute=self.state.get('mute_until',0);self.record_status.setText(('● '+('Kayıt' if recorder.get('kind')=='record' else 'Tekrar tamponu')+f" · {recorder.get('seconds',0)} sn") if recorder.get('active') else 'Kayıt kapalı'+(' · '+recorder['error'] if recorder.get('error') else ''));self.record_status.setStyleSheet('color:#ff718c' if recorder.get('active') else 'color:#b1a1c4')
        self.mute_minutes.setToolTip('Sessiz bitişi: '+str(mute) if mute else 'Sessiz kapalı')
