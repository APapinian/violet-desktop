import json, os, sys, time, subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

def read(path):
    try: return Path(path).read_text().strip()
    except OSError: return ''
def run(*args):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=1)
        return r.stdout.strip() if r.returncode == 0 else ''
    except (OSError, subprocess.TimeoutExpired): return ''
def windows():
    try: return json.loads(read(Path(os.environ.get('XDG_RUNTIME_DIR', '/nonexistent'))/'fatih-qtile.json'))
    except ValueError: return {'active':'1','title':'Masaüstü','groups':[]}
def brightness():
    for d in sorted(Path('/sys/class/backlight').glob('*')):
        try: return round(100*int(read(d/'brightness'))/int(read(d/'max_brightness')))
        except (ValueError, ZeroDivisionError): pass
    return None
def battery():
    for d in sorted(Path('/sys/class/power_supply').glob('*')):
        if read(d/'type') != 'Battery': continue
        try: cap=int(read(d/'capacity'))
        except ValueError: continue
        health=None
        try:
            full=int(read(d/'energy_full') or read(d/'charge_full'))
            design=int(read(d/'energy_full_design') or read(d/'charge_full_design'))
            health=round(100*full/design)
        except (ValueError,ZeroDivisionError): pass
        return dict(battery=cap, charging=read(d/'status')=='Charging',
                    batteryStatus=read(d/'status'), health=health,
                    cycles=read(d/'cycle_count') or '—')
    return dict(battery=None,charging=False,batteryStatus='Unknown',health=None,cycles='—')
def slow():
    return dict(wifi=run('nmcli','-g','GENERAL.CONNECTION','device','show','wlp2s0') or 'Bağlantı yok',
                profile=run('powerprofilesctl','get'))
def media():
    return dict(media=run('playerctl','metadata','--format','{{artist}} · {{title}}'),
                playing=run('playerctl','status')=='Playing')
def welcome(session):
    if not session: return False
    runtime=os.environ.get('XDG_RUNTIME_DIR')
    if not runtime: return False
    marker=Path(runtime)/'fatih-welcome-session'
    if read(marker)==str(session): return False
    try:
        marker.write_text(str(session)); marker.chmod(0o600)
    except OSError: return False
    return True

def watch():
    state={}; last=''; due={}; pending={}; greet=None
    tasks=[('brightness',1,lambda:dict(brightness=brightness())),
           ('media',3,media),('battery',30,battery),('network',20,slow)]
    # Slow CLI calls cannot block Qtile state updates or each other.
    with ThreadPoolExecutor(max_workers=4) as pool:
        while True:
            now=time.monotonic()
            state.update(windows())
            for key, interval, fn in tasks:
                future=pending.get(key)
                if future is not None and future.done():
                    try: state.update(future.result())
                    except Exception: pass
                    pending.pop(key)
                if key not in pending and now>=due.get(key,0):
                    pending[key]=pool.submit(fn);due[key]=now+interval
            if greet is None and state.get('session'):
                greet=welcome(state['session'])
            state['welcome']=greet or False
            line=json.dumps(state,ensure_ascii=False,sort_keys=True)
            if line!=last:
                print(line,flush=True);last=line
            time.sleep(.1)
if __name__=='__main__':
    try:
        if '--watch' in sys.argv: watch()
        else:
            state=windows();state.update(brightness=brightness());state.update(battery());state.update(slow());state.update(media())
            print(json.dumps(state,ensure_ascii=False))
    except (BrokenPipeError,KeyboardInterrupt): pass
