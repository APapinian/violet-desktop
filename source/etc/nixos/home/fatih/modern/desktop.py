#!/usr/bin/env python3
"""One streaming process for the shell. Existing Kingdom remains the media owner."""
import asyncio, json, os, re, subprocess, sys, time
from pathlib import Path
from dbus_next import Message, BusType, MessageType
from dbus_next.aio import MessageBus
import psutil

RUNTIME=Path(os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}'))
SERVICE='me.timschneeberger.GalaxyBudsClient'
DEVICE='/me/timschneeberger/galaxybudsclient/device'
INTERFACE='me.timschneeberger.GalaxyBudsClient.Device'

def run(args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=15)
    if p.returncode:raise RuntimeError(p.stderr.strip() or 'Komut tamamlanamadı')
    return p.stdout.strip()

def unwrap(x):
    if hasattr(x,'value'):return unwrap(x.value)
    if isinstance(x,dict):return {k:unwrap(v) for k,v in x.items()}
    if isinstance(x,list):return [unwrap(v) for v in x]
    return x

async def message(bus,destination,path,interface,member,signature='',body=None):
    answer=await asyncio.wait_for(bus.call(Message(destination=destination,path=path,interface=interface,member=member,signature=signature,body=body or [])),4)
    if answer.message_type==MessageType.ERROR:raise RuntimeError(answer.error_name)
    return unwrap(answer.body[0]) if answer.body else None

def battery(value):
    return int(value) if isinstance(value,(int,float)) and not isinstance(value,bool) and 0<=value<=100 else None

def normalize_galaxy(props):
    # Tmds.DBus emits public properties without the backing-field underscore.
    props={k.lstrip('_'):v for k,v in props.items()}
    return dict(left=battery(props.get('BatteryLeft')),right=battery(props.get('BatteryRight')),
        case=battery(props.get('BatteryCase')),address=props.get('Address'),name=props.get('Name'),model=props.get('Model'),
        leftState=props.get('WearStateLeft'),rightState=props.get('WearStateRight'),source='Galaxy Buds Client')

async def bluetooth():
    result=dict(items=[],buds=dict(connected=False,left=None,right=None,case=None,battery=None,name='Galaxy Buds 3 Pro',source='Veri yok'))
    bus=None;session=None
    try:
        bus=await MessageBus(bus_type=BusType.SYSTEM).connect()
        rows=await message(bus,'org.bluez','/','org.freedesktop.DBus.ObjectManager','GetManagedObjects')
        for path,ifs in rows.items():
            d=ifs.get('org.bluez.Device1')
            if not d:continue
            name=d.get('Alias') or d.get('Name') or 'Bluetooth'
            row=dict(name=name,address=d.get('Address'),connected=d.get('Connected',False),paired=d.get('Paired',False),trusted=d.get('Trusted',False),battery=battery(ifs.get('org.bluez.Battery1',{}).get('Percentage')))
            if row['paired'] or row['connected']:result['items'].append(row)
        choices=[x for x in result['items'] if 'buds' in x['name'].lower()]
        choices.sort(key=lambda x:(not x['connected'],'3' not in x['name']))
        if choices:result['buds'].update(choices[0],source='BlueZ')
    except Exception:result['error']='Bluetooth servisine erişilemiyor'
    finally:
        if bus:bus.disconnect()
    try:
        session=await MessageBus().connect()
        props=await message(session,SERVICE,DEVICE,'org.freedesktop.DBus.Properties','GetAll','s',[INTERFACE])
        galaxy=normalize_galaxy(props)
        # Never merge a different headset into the selected BlueZ device.
        selected=result['buds'].get('address')
        if galaxy.get('address') and (not selected or galaxy['address'].upper()==selected.upper()):
            result['buds'].update(galaxy,connected=True)
    except Exception:pass
    finally:
        if session:session.disconnect()
    return result

async def watch():
    bt={};last=0
    while True:
        now=time.monotonic()
        if now-last>8:
            bt=await bluetooth();last=now
        status=dict(version=1,bluetooth=bt,cpu=psutil.cpu_percent(),memory=psutil.virtual_memory().percent,
            disk=psutil.disk_usage(str(Path.home())).percent,uptime=int(time.time()-psutil.boot_time()),updated=time.time())
        print(json.dumps(status,ensure_ascii=False),flush=True)
        await asyncio.sleep(1)

def buds_connect(address,disconnect=False):
    if not re.fullmatch(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}',str(address)):raise ValueError('Önce Buds cihazını Bluetooth menüsünden eşleştir')
    rows=asyncio.run(bluetooth())['items']
    device=next((x for x in rows if x['address']==address and x['paired']),None)
    if not device:raise ValueError('Bu cihaz eşleştirilmemiş')
    if disconnect:return run(['bluetoothctl','disconnect',address])
    run(['bluetoothctl','trust',address]);run(['bluetoothctl','connect',address])
    return 'Buds bağlandı. Ses çıkışı panelinden kulaklığı seçebilirsin.'

def audio_profile(address,mode):
    if mode not in ('music','call'):raise ValueError('Ses profili geçersiz')
    cards=json.loads(run(['pactl','-f','json','list','cards']))
    card=next((c for c in cards if c.get('properties',{}).get('api.bluez5.address','').upper()==str(address).upper() or str(address).replace(':','_').upper() in c['name'].upper()),None)
    if not card:raise ValueError('Buds ses aygıtı henüz hazır değil')
    profiles=card.get('profiles',{})
    if isinstance(profiles,list):profiles={p['name']:p for p in profiles}
    candidates=[k for k,v in profiles.items() if (k.startswith('a2dp-sink') if mode=='music' else k.startswith('headset-head-unit')) and v.get('available')!='no']
    if not candidates:raise ValueError('İstenen ses profili cihazda sunulmuyor')
    candidates.sort(key=lambda k:('aac' not in k if mode=='music' else 'msbc' not in k))
    run(['pactl','set-card-profile',card['name'],candidates[0]])
    return 'Müzik profili seçildi' if mode=='music' else 'Mikrofon profili seçildi'

def main():
    action=sys.argv[1] if len(sys.argv)>1 else 'watch'
    if action=='watch':asyncio.run(watch());return
    if action=='pick-music':
        from PyQt6.QtWidgets import QApplication,QFileDialog,QMessageBox
        app=QApplication(sys.argv)
        files=QFileDialog.getOpenFileNames(None,'Müzik dosyalarını seç',str(Path.home()),'Ses (*.mp3 *.flac *.ogg *.opus *.m4a *.wav *.aac);;Tüm dosyalar (*)')[0]
        if files:
            try:
                result=json.loads(run(['kingdomctl','play-local',json.dumps(files)]))
                if not result.get('ok'):raise RuntimeError(result.get('error','Oynatılamadı'))
            except Exception as e:QMessageBox.warning(None,'Müzik açılamadı',str(e))
        return
    value=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
    try:
        if action in ('buds-connect','buds-disconnect'):result=buds_connect(value.get('address'),action.endswith('disconnect'))
        elif action=='buds-profile':result=audio_profile(value.get('address'),value.get('mode'))
        elif action=='player':
            player=value.get('player');cmd=value.get('command')
            if not isinstance(player,str) or not player or player.startswith('-'):raise ValueError('Oynatıcı bulunamadı')
            if cmd=='seek':args=['position',str(max(0,float(value['seconds'])))]
            elif cmd=='shuffle':args=['shuffle','Toggle']
            elif cmd=='loop':args=['loop',value['mode']] if value.get('mode') in ('None','Track','Playlist') else []
            elif cmd in ('play-pause','next','previous','stop'):args=[cmd]
            else:args=[]
            if not args:raise ValueError('Oynatıcı komutu geçersiz')
            result=run(['playerctl','--player='+player]+args)
        else:raise ValueError('Bilinmeyen işlem')
        print(json.dumps(dict(ok=True,result=result),ensure_ascii=False))
    except Exception as e:print(json.dumps(dict(ok=False,error=str(e)),ensure_ascii=False));sys.exit(1)
if __name__=='__main__':
    try:main()
    except BrokenPipeError:pass
