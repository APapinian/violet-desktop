"""Compatible with MyBrain's Rust PortableVault, format MYBRN001 / manifest v1."""
import copy, datetime as dt, fcntl, hashlib, json, os, tempfile, uuid
from pathlib import Path
from argon2.low_level import hash_secret_raw, Type
from nacl.bindings import crypto_aead_xchacha20poly1305_ietf_encrypt, crypto_aead_xchacha20poly1305_ietf_decrypt

MAGIC=b'MYBRN001'
class Conflict(RuntimeError):pass

def key(password,salt):
    return hash_secret_raw(password.encode('utf-8'),salt,time_cost=2,memory_cost=19456,parallelism=1,hash_len=32,type=Type.ID,version=19)

def encrypt(plain,password):
    salt=os.urandom(16);nonce=os.urandom(24)
    return MAGIC+salt+nonce+crypto_aead_xchacha20poly1305_ietf_encrypt(plain,None,nonce,key(password,salt))

def decrypt(blob,password):
    if blob[:8]!=MAGIC or len(blob)<64:raise ValueError('MyBrain kasa biçimi geçersiz')
    try:return crypto_aead_xchacha20poly1305_ietf_decrypt(blob[48:],None,blob[24:48],key(password,blob[8:24]))
    except Exception as e:raise ValueError('Parola yanlış veya kasa bozuk') from e

def atomic(path,content):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(content);f.flush();os.fsync(f.fileno())
        os.replace(name,path)
        fd=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        if os.path.exists(name):os.unlink(name)

def dump(data):return json.dumps(data,ensure_ascii=False,allow_nan=False,indent=2).encode('utf-8')
def digest(blob):return hashlib.sha256(blob).hexdigest()
def resolve(chosen):
    root=Path(chosen).expanduser().resolve()
    return root if (root/'vault.json').is_file() or root.name=='data' else root/'data'

class Vault:
    def __init__(self,root,password):self.root=resolve(root);self.password=password;self.manifest={};self.data={}
    def load(self):
        manifest=json.loads((self.root/'vault.json').read_bytes())
        if manifest.get('format_version')!=1 or manifest.get('active_slot') not in ('a','b'):raise ValueError('Desteklenmeyen kasa sürümü')
        blob=(self.root/f'database/vault-{manifest["active_slot"]}.mbdb').read_bytes()
        if digest(blob)!=manifest['database_hash']:raise ValueError('Kasa bütünlük kontrolü başarısız')
        data=json.loads(decrypt(blob,self.password))
        if not isinstance(data,dict) or data.get('schema_version')!=2:raise ValueError('Desteklenmeyen MyBrain veri şeması')
        self.manifest=manifest;self.data=data;return data
    def create(self,collections):
        if len(self.password)<4:raise ValueError('Parola en az dört karakter olmalı')
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        # Reservation prevents two Python creators from replacing a live vault.
        reserve=self.root/'vault.json'
        with reserve.open('xb') as f:f.write(b'{}')
        try:
            data=dict(schema_version=2,settings={},**{k:[] for k in collections})
            blob=encrypt(dump(data),self.password)
            manifest=dict(vault_id=str(uuid.uuid4()),format_version=1,active_slot='a',revision=1,last_writer='python-desktop',database_hash=digest(blob),updated_at=dt.datetime.now(dt.timezone.utc).isoformat())
            atomic(self.root/'database/vault-a.mbdb',blob);atomic(reserve,dump(manifest));self.manifest=manifest;self.data=data
        except Exception:reserve.unlink(missing_ok=True);raise
    def save(self,data):
        # Rust does not honor this advisory lock; close its window before Python edits.
        with (self.root/'.python-writer.lock').open('a+b') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            before=(self.root/'vault.json').read_bytes();disk=json.loads(before)
            if disk['revision']!=self.manifest['revision'] or disk['database_hash']!=self.manifest['database_hash']:raise Conflict('Kasa başka uygulamada değişti. Kilitleyip yeniden aç; değişiklik uygulanmadı.')
            blob=encrypt(dump(data),self.password)
            if (self.root/'vault.json').read_bytes()!=before:raise Conflict('Kasa kayıt sırasında değişti; değişiklik uygulanmadı.')
            active=self.root/f'database/vault-{disk["active_slot"]}.mbdb'
            old_blob=active.read_bytes()
            if digest(old_blob)!=disk['database_hash']:raise ValueError('Mevcut kasa bütünlüğü bozuk')
            backup=self.root/'backups'/f'python-{disk["revision"]}-{uuid.uuid4().hex[:8]}'
            atomic(backup/'vault.json',before);atomic(backup/f'database/vault-{disk["active_slot"]}.mbdb',old_blob)
            slot='b' if disk['active_slot']=='a' else 'a'
            target=self.root/f'database/vault-{slot}.mbdb';atomic(target,blob)
            if digest(target.read_bytes())!=digest(blob):raise OSError('USB kayıt doğrulaması başarısız')
            manifest=dict(disk,active_slot=slot,revision=disk['revision']+1,last_writer='python-desktop',database_hash=digest(blob),updated_at=dt.datetime.now(dt.timezone.utc).isoformat())
            atomic(self.root/'vault.json',dump(manifest));self.manifest=manifest;self.data=copy.deepcopy(data)
    def put_asset(self,path):
        path=Path(path)
        if path.stat().st_size>24*1024*1024:raise ValueError('Ek dosya en fazla 24 MiB olabilir')
        ident=str(uuid.uuid4());atomic(self.root/f'assets/{ident}.mbasset',encrypt(path.read_bytes(),self.password))
        return f'asset:{ident}:{path.name.replace(":","_")}'
    def get_asset(self,reference):
        parts=reference.split(':',2)
        if len(parts)!=3 or parts[0]!='asset':raise ValueError('Ek dosya başvurusu geçersiz')
        ident=str(uuid.UUID(parts[1]));return decrypt((self.root/f'assets/{ident}.mbasset').read_bytes(),self.password)
