import json,sys,os
from pathlib import Path
from PyQt6.QtCore import QObject,QRunnable,QThreadPool,pyqtSignal,Qt
from PyQt6.QtGui import QShortcut,QKeySequence,QPainter,QLinearGradient,QColor,QFont
from PyQt6.QtWidgets import *
import core

class Signals(QObject):finished=pyqtSignal(object,object)
class Job(QRunnable):
    def __init__(self,fn):super().__init__();self.fn=fn;self.signals=Signals()
    def run(self):
        try:value,error=self.fn(),None
        except Exception as e:value,error=None,str(e)
        self.signals.finished.emit(value,error)

class Banner(QWidget):
    def __init__(self,title,subtitle):super().__init__();self.title=title;self.subtitle=subtitle;self.setMinimumHeight(118)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);g=QLinearGradient(0,0,self.width(),110);g.setColorAt(0,QColor('#49315e'));g.setColorAt(1,QColor('#161922'));p.setPen(Qt.PenStyle.NoPen);p.setBrush(g);p.drawRoundedRect(self.rect(),24,24);p.setPen(QColor('#deccff'));p.setFont(QFont('DejaVu Serif',23));p.drawText(28,52,'✦  '+self.title);p.setFont(QFont('Rubik',11));p.setPen(QColor('#b3a5c7'));p.drawText(30,86,self.subtitle)

class Window(QWidget):
    def __init__(self,title):
        super().__init__();self.setWindowTitle('Violet · '+title);self.resize(790,730);self.jobs=set();self.outer=QVBoxLayout(self);self.outer.setContentsMargins(24,24,24,24);self.outer.setSpacing(16);QShortcut(QKeySequence('Escape'),self,activated=self.close)
    def work(self,fn,done):
        job=Job(fn);self.jobs.add(job)
        def finish(value,error):
            self.jobs.discard(job)
            if error:QMessageBox.warning(self,'Violet',error)
            else:done(value)
        job.signals.finished.connect(finish);QThreadPool.globalInstance().start(job)

class Agent(Window):
    def __init__(self):
        super().__init__('AI yardımcısı');self.messages=[];self.proposal=None;self.busy=False
        self.outer.addWidget(Banner('Krallığın yardımcısı','Kısa cevaplar · İncelenebilir masaüstü işlemleri'))
        tabs=QTabWidget();self.outer.addWidget(tabs,1);chat=QWidget();l=QVBoxLayout(chat);l.setSpacing(14);tabs.addTab(chat,'Sohbet')
        self.log=QTextBrowser();self.log.setOpenExternalLinks(False);l.addWidget(self.log,1)
        self.input=QPlainTextEdit();self.input.setPlaceholderText('Sesi %30 yap, Firefox’u aç, kısa bir metni düzenle…');self.input.setMaximumHeight(100);l.addWidget(self.input)
        self.send=QPushButton('Gönder  ·  Ctrl+Enter');self.send.clicked.connect(self.send_message);l.addWidget(self.send)
        QShortcut(QKeySequence('Ctrl+Return'),self,activated=self.send_message)
        self.apply=QPushButton('Önerilen işlemi uygula');self.apply.setEnabled(False);self.apply.clicked.connect(self.perform);l.addWidget(self.apply)
        self.usage=QLabel('API anahtarını Ayarlar’dan ekle.');l.addWidget(self.usage)
        page=QWidget();f=QFormLayout(page);tabs.addTab(page,'Ayarlar');saved=core.load('openai.json');self.key=QLineEdit(saved.get('api_key',''));self.key.setEchoMode(QLineEdit.EchoMode.Password);f.addRow('OpenAI API anahtarı',self.key);self.model=QLineEdit(saved.get('model','gpt-5.6-luna'));f.addRow('Model',self.model)
        save=QPushButton('Ayarları kaydet');save.clicked.connect(self.settings_save);f.addRow(save);info=QLabel('Yalnız yazdığın son 8 mesaj API’ye gönderilir. Dosyalar, açık pencere başlıkları ve kasa içeriği gönderilmez. Bir istekte çıktı sınırı 800 token. API kullanımı ayrı ücretlendirilir.');info.setWordWrap(True);f.addRow(info)
        self.log.setPlainText('Violet yardımcısı hazır. Genel soruları yanıtlayabilir ve sınırlı masaüstü işlemleri önerebilirim.')
    def settings_save(self):
        try:core.save('openai.json',{'api_key':self.key.text().strip(),'model':self.model.text().strip()});self.usage.setText('Ayarlar kaydedildi.')
        except Exception as e:QMessageBox.warning(self,'Ayarlar',str(e))
    def send_message(self):
        text=self.input.toPlainText().strip()
        if not text or self.busy:return
        if len(text)>8000:QMessageBox.warning(self,'Violet','Bir mesaj en fazla 8000 karakter.');return
        try:settings=core.load('openai.json')
        except Exception as e:QMessageBox.warning(self,'Ayarlar',str(e));return
        self.busy=True;self.send.setEnabled(False);self.apply.setEnabled(False);self.proposal=None;self.messages.append({'role':'user','content':text});self.log.append('');self.log.insertPlainText('Sen: '+text+'\n');self.input.clear()
        job=Job(lambda:core.ask(self.messages,settings));self.jobs.add(job)
        def done(value,error):
            self.jobs.discard(job);self.busy=False;self.send.setEnabled(True)
            if error:self.log.insertPlainText('Hata: '+error+'\n');return
            self.messages.append({'role':'assistant','content':value['answer']});self.messages=self.messages[-8:];self.log.insertPlainText('Violet: '+value['answer']+'\n');self.proposal=value;self.apply.setText('Uygula: '+value['action']+(f" → %{value['value']}" if value['action'] in ('volume','brightness') else ''));self.apply.setEnabled(value['action']!='none');u=value['usage'];self.usage.setText(f"Son istek: {u.get('input_tokens',0)} girdi · {u.get('output_tokens',0)} çıktı token")
        job.signals.finished.connect(done);QThreadPool.globalInstance().start(job)
    def perform(self):
        if not self.proposal:return
        proposal=self.proposal;self.apply.setEnabled(False);self.work(lambda:core.execute(proposal['action'],proposal['value']),lambda result:self.log.insertPlainText('Sonuç: '+result+'\n'))

class Remote(Window):
    def __init__(self):
        super().__init__('Telegram / SSH');self.outer.addWidget(Banner('Uzaktan kontrol','Telegram komutları ve SSH anahtar alanı'));self.fields={};saved=core.load('remote.json');f=QFormLayout();self.outer.addLayout(f)
        for name,label,value in [('token','Telegram bot token',saved.get('token','')),('users','İzinli kullanıcı ID’leri',','.join(map(str,saved.get('users',[])))),('chats','İzinli sohbet ID’leri',','.join(map(str,saved.get('chats',[]))))]:
            field=QLineEdit(value);self.fields[name]=field;f.addRow(label,field)
        self.fields['token'].setEchoMode(QLineEdit.EchoMode.Password)
        for label,fn in [('Ayarları kaydet',self.settings_save),('Botu başlat',lambda:self.service('start')),('Botu durdur',lambda:self.service('stop')),('Otomatik başlatmayı aç',lambda:self.service('enable')),('Otomatik başlatmayı kapat',lambda:self.service('disable'))]:b=QPushButton(label);b.clicked.connect(fn);self.outer.addWidget(b)
        label=QLabel('Bot: /status /play /next /previous /volume 0-100 /brightness 0-100 /lock\nYalnız hem kullanıcı hem sohbet kimliği eşleşen komutlar çalışır. SSH anahtarlı erişim hazırdır; port güvenlik duvarında otomatik açılmaz.');label.setWordWrap(True);self.outer.addWidget(label)
        self.public=QPlainTextEdit();self.public.setMaximumHeight(80);self.public.setPlaceholderText('SSH açık anahtarını buraya yapıştır: ssh-ed25519 AAAA…');self.outer.addWidget(self.public);b=QPushButton('SSH açık anahtarını ekle');b.clicked.connect(self.add_key);self.outer.addWidget(b);self.message=QLabel('Bot yapılandırılana kadar kapalı.');self.outer.addWidget(self.message)
    def settings_save(self):
        try:
            val={'token':self.fields['token'].text().strip(),'users':[int(x.strip()) for x in self.fields['users'].text().split(',') if x.strip()],'chats':[int(x.strip()) for x in self.fields['chats'].text().split(',') if x.strip()]}
            if not val['users'] or not val['chats']:raise ValueError('Kullanıcı ve sohbet kimliği gerekli')
            core.save('remote.json',val);self.message.setText('Kaydedildi; çalışan bot için durdur ve başlat.')
        except Exception as e:QMessageBox.warning(self,'Ayarlar',str(e))
    def service(self,verb):
        if verb in ('start','enable'):
            try:
                saved=core.load('remote.json')
                if not saved.get('token') or not saved.get('users') or not saved.get('chats'):raise ValueError('Önce bot ayarlarını kaydet')
            except Exception as e:QMessageBox.warning(self,'Bot',str(e));return
        self.work(lambda:core.run(['systemctl','--user',verb,'violet-telegram.service']),lambda _:self.message.setText('Bot servisi: '+verb))
    def add_key(self):
        import re
        key=self.public.toPlainText().strip()
        if '\n' in key or not re.fullmatch(r'(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+(?: [^\r\n]+)?',key):QMessageBox.warning(self,'SSH','Geçerli bir açık anahtar gerekli.');return
        try:
            directory=Path.home()/'.ssh';directory.mkdir(mode=0o700,exist_ok=True);path=directory/'authorized_keys'
            if directory.is_symlink() or path.is_symlink():raise ValueError('SSH yolları sembolik bağ olamaz')
            old=path.read_text() if path.exists() else ''
            if key not in old.splitlines():
                fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
                with os.fdopen(fd,'w') as f:f.write(('\n' if old and not old.endswith('\n') else '')+key+'\n')
            os.chmod(directory,0o700);os.chmod(path,0o600);self.public.clear();self.message.setText('Açık anahtar eklendi. SSH portu: 22')
        except Exception as e:QMessageBox.warning(self,'SSH',str(e))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='bot':core.bot_loop()
    else:
        app=QApplication(sys.argv);app.setApplicationName('violet-agent');app.setStyle('Fusion');app.setStyleSheet(Path(__file__).with_name('violet.qss').read_text());window=Remote() if len(sys.argv)>1 and sys.argv[1]=='remote' else Agent();window.show();sys.exit(app.exec())
