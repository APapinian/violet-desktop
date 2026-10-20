"""Single native instance; lock acknowledgment is used before USB eject."""
import json,os,stat
from pathlib import Path
from PyQt6.QtCore import QTimer
from PyQt6.QtNetwork import QLocalServer,QLocalSocket
from PyQt6.QtWidgets import QApplication,QDialog

def endpoint():
    root=Path(os.environ.get('XDG_RUNTIME_DIR','/run/user/'+str(os.getuid())))/'violet-desktop';root.mkdir(mode=0o700,exist_ok=True)
    if root.is_symlink() or root.stat().st_uid!=os.getuid():raise ValueError('MyBrain IPC yolu geçersiz')
    os.chmod(root,0o700);return str(root/'brain.sock')

def publish(locked):
    import tempfile,uuid
    root=Path(endpoint()).parent
    value={'locked':bool(locked),'generation':uuid.uuid4().hex,'pid':os.getpid()}
    fd,path=tempfile.mkstemp(prefix='.brain-',dir=root)
    try:
        with os.fdopen(fd,'w') as f:os.fchmod(f.fileno(),0o600);json.dump(value,f)
        os.replace(path,root/'brain-state.json')
    finally:
        if os.path.exists(path):os.unlink(path)

def forward(path=''):
    sock=QLocalSocket();sock.connectToServer(endpoint())
    if not sock.waitForConnected(250):return False
    sock.write((json.dumps({'action':'open','path':path})+'\n').encode());sock.flush();sock.waitForBytesWritten(250);sock.waitForReadyRead(1000);sock.disconnectFromServer();return True

class BrainServer:
    def __init__(self,brain):
        publish(brain.vault is None)
        self.brain=brain;self.server=QLocalServer(brain);path=Path(endpoint())
        if path.exists():
            if not stat.S_ISSOCK(path.lstat().st_mode) or path.lstat().st_uid!=os.getuid():raise ValueError('MyBrain IPC yolu geçersiz')
            QLocalServer.removeServer(str(path))
        self.server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        if not self.server.listen(str(path)):raise ValueError(self.server.errorString())
        os.chmod(path,0o600);self.server.newConnection.connect(self.accept)
    def accept(self):
        while self.server.hasPendingConnections():
            sock=self.server.nextPendingConnection();sock._brain_buffer=b'';sock.readyRead.connect(lambda s=sock:self.read(s));sock.disconnected.connect(sock.deleteLater);QTimer.singleShot(2000,sock.disconnectFromServer)
    def read(self,sock):
        sock._brain_buffer+=bytes(sock.readAll())
        if len(sock._brain_buffer)>262144:sock.disconnectFromServer();return
        if b'\n' not in sock._brain_buffer:return
        try:
            r=json.loads(sock._brain_buffer.split(b'\n',1)[0]);b=self.brain
            if r['action']=='status':data={'root':str(b.vault.root) if b.vault else None,'pid':os.getpid(),'locked':b.vault is None}
            elif r['action']=='lock':
                # Closing a form discards its uncommitted edits; never saves behind the user.
                b.lock();data='Kasa kilitlendi'
            elif r['action']=='open':
                path=r.get('path','')
                if path:
                    from vault import resolve
                    target=resolve(path)
                    if not (target/'vault.json').is_file():raise ValueError('Kasa bulunamadı')
                    if b.vault and b.vault.root!=target:raise ValueError('Diğer kasayı önce kilitle')
                    if not b.vault:b.path.setText(str(target))
                b.showNormal();b.raise_();b.activateWindow();data='MyBrain açıldı'
            elif r['action'] in ('search','open-record','quick-note','attach'):
                if not b.vault:raise ValueError('MyBrain kasası kilitli')
                from app import META,title,text,today
                import copy,uuid
                action=r['action']
                if action=='search':
                    query=str(r.get('query','')).casefold().strip();data=[]
                    if len(query)>=2:
                        for collection in META['schema']:
                            for row in b.data.get(collection,[]):
                                if isinstance(row,dict) and query in json.dumps(row,ensure_ascii=False).casefold():
                                    data.append({'collection':collection,'id':row.get('id'),'title':title(row)[:180]})
                                    if len(data)>=30:break
                            if len(data)>=30:break
                elif action=='open-record':
                    collection=r.get('collection');ident=r.get('id')
                    if collection not in META['schema'] or not any(x.get('id')==ident for x in b.data.get(collection,[])):raise ValueError('Kayıt bulunamadı')
                    b.search.clear();b.navigate(collection)
                    for i,item in enumerate(b.ids):
                        if item==(collection,ident):b.table.selectRow(i);break
                    b.showNormal();b.raise_();b.activateWindow();data='Kayıt açıldı'
                else:
                    body=str(r.get('body',''));heading=str(r.get('title','Hızlı not')).strip() or 'Hızlı not'
                    if len(body)>100000 or len(heading)>300:raise ValueError('Not fazla büyük')
                    record={'id':str(uuid.uuid4()),'title':heading,'body':body,'date':today()}
                    if action=='attach':
                        paths=r.get('paths',[])
                        if not isinstance(paths,list) or not 0<len(paths)<=20:raise ValueError('1–20 dosya seç')
                        selected=[]
                        for raw in paths:
                            path=Path(raw).expanduser()
                            if path.is_symlink() or not path.is_file() or path.stat().st_size>24*1024*1024:raise ValueError('Ek normal ve en çok 24 MiB olmalı')
                            selected.append(path)
                        record['attachments']=[b.vault.put_asset(path) for path in selected]
                        record['body']='Ekler: '+', '.join(path.name for path in selected)
                        record['title']='Dosyalar · '+selected[0].name
                    value=copy.deepcopy(b.data);value.setdefault('notes',[]).append(record)
                    if not b.commit(value):raise ValueError('Not kaydedilemedi')
                    data='MyBrain notu şifreli kasaya kaydedildi'
            else:raise ValueError('MyBrain işlemi geçersiz')
            response={'ok':True,'data':data}
        except Exception as e:response={'ok':False,'error':str(e)}
        sock.write((json.dumps(response)+'\n').encode());sock.flush();sock.disconnectFromServer()
