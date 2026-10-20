"""Shared local state, bounded HTTP, and argument-safe desktop commands."""
import json
import os
import re
import sqlite3
import subprocess
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))/'fatih-kingdom'
STATE = Path(os.environ.get('XDG_STATE_HOME', Path.home()/'.local/state'))/'fatih-kingdom'
RUNTIME = Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp'))/('fatih-kingdom' if os.environ.get('XDG_RUNTIME_DIR') else 'fatih-kingdom-'+str(os.getuid()))
for p in (CONFIG, STATE, RUNTIME):
    p.mkdir(parents=True, exist_ok=True, mode=0o700)


def atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_name(path.name+'.'+str(threading.get_ident())+'.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False))
    temp.chmod(0o600)
    temp.replace(path)


def load(path, default=None):
    try: return json.loads(Path(path).read_text())
    except (OSError, ValueError): return {} if default is None else default


def validate_settings(value, partial=False):
    default=load(Path(__file__).with_name('defaults.json'))
    def check(actual, expected, path):
        if expected is None:
            if actual is not None and (type(actual) not in (int,float)):raise ValueError(path+': sayı gerekli')
        elif isinstance(expected,dict):
            if not isinstance(actual,dict):raise ValueError(path+': nesne gerekli')
            if path=='settings.groupLayouts':
                if not all(isinstance(k,str) and isinstance(v,str) for k,v in actual.items()):raise ValueError('groupLayouts: metin eşleşmesi gerekli')
                return
            for k,v in actual.items():
                if k not in expected:raise ValueError(path+'.'+k+': bilinmeyen ayar; sırları secrets.env içine yaz')
                check(v,expected[k],path+'.'+k)
        elif isinstance(expected,list):
            if not isinstance(actual,list) or len(actual)>100:raise ValueError(path+': en fazla 100 öğeli dizi gerekli')
        elif type(expected) is bool:
            if type(actual) is not bool:raise ValueError(path+': true/false gerekli')
        elif isinstance(expected,(int,float)):
            if type(actual) not in (int,float):raise ValueError(path+': sayı gerekli')
        elif not isinstance(actual,str):raise ValueError(path+': metin gerekli')
    if not isinstance(value,dict) or value.get('version')!=1:raise ValueError('Ayar sürümü 1 gerekli')
    check(value,default,'settings')
    for k in ('youtube','news','podcasts'):
        for item in value.get('feeds',{}).get(k,[]):
            if k=='youtube' and isinstance(item,str):continue
            if not isinstance(item,dict) or (k=='youtube' and not isinstance(item.get('id'),str)) or (k!='youtube' and not all(isinstance(item.get(x),str) for x in ('name','url'))):raise ValueError('RSS kaynak alanları hatalı')
    for path,items in [('subreddits',value.get('feeds',{}).get('subreddits',[])),('stocks',value.get('finance',{}).get('stocks',[])),('crypto',value.get('finance',{}).get('crypto',[])),('twitch',value.get('twitch',{}).get('channels',[])),('files',value.get('calendar',{}).get('files',[])),('urls',value.get('calendar',{}).get('urls',[])),('goals',value.get('goals',[])),('translation',value.get('translation',{}).get('command',[])),('games',value.get('games',{}).get('classes',[]) )]:
        if not all(isinstance(x,str) for x in items):raise ValueError(path+': metin dizisi gerekli')
    for name,required in [('commands',('id','name','argv')),('applicationRules',('pattern',)),('radios',('name','url')),('tasks',('id','text')),('dailyWords',('text',))]:
        for item in value.get(name,[]):
            if not isinstance(item,dict) or not all(k in item for k in required):raise ValueError(name+': gerekli alanlar '+','.join(required))
    loc=value.get('location',{})
    from zoneinfo import ZoneInfo
    try:ZoneInfo(loc.get('timezone','Europe/Istanbul'))
    except Exception:raise ValueError('Geçerli saat dilimi gerekli')
    for k,limit in [('latitude',90),('longitude',180)]:
        if loc.get(k) is not None and not -limit<=loc[k]<=limit:raise ValueError('Konum aralığı hatalı')
    return value


def settings():
    default = load(Path(__file__).with_name('defaults.json'))
    def merge(a, b):
        for k, v in b.items():
            if isinstance(v, dict) and isinstance(a.get(k), dict): merge(a[k], v)
            else: a[k] = v
        return a
    custom=load(CONFIG/'settings.json')
    if custom:
        try:validate_settings(custom,partial=True)
        except ValueError:return default
    return merge(default, custom)


def run(args, timeout=6, input=None):
    r = subprocess.run(args, input=input, text=True, capture_output=True, timeout=timeout)
    if r.returncode: raise RuntimeError('Komut başarısız: '+Path(args[0]).name)
    return r.stdout.strip()


def detach(args):
    return subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=True)


def http(url, headers=None, limit=4*1024*1024):
    import requests
    if urlparse(url).scheme not in ('https', 'http'): raise ValueError('HTTP adresi gerekli')
    with requests.get(url, headers={'User-Agent':'FatihKingdom/1.0 (personal desktop)', **(headers or {})},
                      timeout=(5, 12), stream=True) as r:
        r.raise_for_status()
        chunks, size = [], 0
        for chunk in r.iter_content(65536):
            size += len(chunk)
            if size > limit: raise ValueError('Yanıt boyutu sınırı')
            chunks.append(chunk)
        return b''.join(chunks)


def get_json(url, headers=None): return json.loads(http(url, headers))


def safe_url(url):
    if not isinstance(url, str) or urlparse(url).scheme not in ('http', 'https'): raise ValueError('Geçersiz URL')
    return url


class NeedsConfig(Exception): pass


class Store:
    def __init__(self, path=STATE/'data.sqlite'):
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS cache (name TEXT PRIMARY KEY, data TEXT, updated REAL, status TEXT, error TEXT);
          CREATE TABLE IF NOT EXISTS items (source TEXT, id TEXT, data TEXT, seen INTEGER, first REAL, PRIMARY KEY(source,id));
          CREATE TABLE IF NOT EXISTS initialized (source TEXT PRIMARY KEY);
          CREATE TABLE IF NOT EXISTS prices (symbol TEXT, timestamp REAL, value REAL);
        ''')
        self.db.commit()

    def put(self, name, data, status='ready', error=''):
        with self.lock, self.db:
            if status != 'ready':
                old = self.get(name)
                data, timestamp = old.get('data'), old.get('updated', 0)
            else: timestamp = time.time()
            self.db.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?,?,?)',
                            (name, json.dumps(data, ensure_ascii=False), timestamp, status, error))

    def get(self, name):
        with self.lock:
            row = self.db.execute('SELECT data,updated,status,error FROM cache WHERE name=?', (name,)).fetchone()
        return dict(data=json.loads(row[0]), updated=row[1], status=row[2], error=row[3], stale=row[2]!='ready') if row else dict(data=None,updated=0,status='waiting',error='',stale=False)

    def all(self):
        with self.lock: names=[r[0] for r in self.db.execute('SELECT name FROM cache')]
        return {n:self.get(n) for n in names}

    def feed(self, source, entries):
        with self.lock, self.db:
            initial = self.db.execute('SELECT 1 FROM initialized WHERE source=?', (source,)).fetchone() is None
            fresh=[]
            for e in entries:
                ident=str(e['id'])
                if not self.db.execute('SELECT 1 FROM items WHERE source=? AND id=?', (source,ident)).fetchone():
                    self.db.execute('INSERT INTO items VALUES (?,?,?,?,?)',(source,ident,json.dumps(e,ensure_ascii=False),int(initial),time.time()))
                    if not initial:fresh.append(e)
            self.db.execute('INSERT OR IGNORE INTO initialized VALUES (?)',(source,))
            count=self.db.execute('SELECT count(*) FROM items WHERE source=? AND seen=0',(source,)).fetchone()[0]
            self.db.execute('DELETE FROM items WHERE source=? AND seen=1 AND first<?',(source,time.time()-30*86400))
            return count,fresh

    def mark(self, source):
        with self.lock,self.db:self.db.execute('UPDATE items SET seen=1 WHERE source=?',(source,))

    def history(self, symbol, value=None):
        with self.lock,self.db:
            if value is not None:
                self.db.execute('INSERT INTO prices VALUES (?,?,?)',(symbol,time.time(),value))
                self.db.execute('DELETE FROM prices WHERE timestamp<?',(time.time()-7*86400,))
            return [r[0] for r in self.db.execute('SELECT value FROM prices WHERE symbol=? ORDER BY timestamp DESC LIMIT 48',(symbol,))][::-1]
