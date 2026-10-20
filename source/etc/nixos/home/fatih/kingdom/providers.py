"""Read-only providers. Missing accounts/settings are explicit, never fake zeroes."""
import asyncio
import datetime as dt
import hashlib
import imaplib
import json
import math
import os
import re
import shutil
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode, quote
from zoneinfo import ZoneInfo
from common import CONFIG, STATE, RUNTIME, NeedsConfig, get_json, http, run, safe_url


def location(c):
    p=c['location']
    if p.get('latitude') is None or p.get('longitude') is None:raise NeedsConfig('Ayarlar → şehir seç')
    lat,lon=float(p['latitude']),float(p['longitude'])
    if not -90<=lat<=90 or not -180<=lon<=180:raise ValueError('Koordinat aralığı')
    return dict(latitude=lat,longitude=lon,timezone=p.get('timezone','Europe/Istanbul'))


def weather(c, store):
    p=location(c);p.update(current='temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m',
        daily='temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset',forecast_days=5)
    return get_json('https://api.open-meteo.com/v1/forecast?'+urlencode(p))


def aqi(c,store):
    p=location(c);p.update(current='european_aqi,pm2_5,pm10')
    return get_json('https://air-quality-api.open-meteo.com/v1/air-quality?'+urlencode(p))


def prayer(c,store):
    p=location(c);p.update(method=int(c['prayer']['method']),school=int(c['prayer']['school']))
    p['timezonestring']=p.pop('timezone')
    now=dt.datetime.now(ZoneInfo(p['timezonestring']))
    result=[]
    for day in (now.date(),now.date()+dt.timedelta(days=1)):
        r=get_json('https://api.aladhan.com/v1/timings/'+day.strftime('%d-%m-%Y')+'?'+urlencode(p))['data']
        for key,label in [('Fajr','İmsak'),('Sunrise','Güneş'),('Dhuhr','Öğle'),('Asr','İkindi'),('Maghrib','Akşam'),('Isha','Yatsı')]:
            tm=r['timings'][key].split(' ')[0]
            value=dt.datetime.fromisoformat(str(day)+'T'+tm).replace(tzinfo=ZoneInfo(p['timezonestring']))
            result.append(dict(name=label,time=tm,timestamp=value.timestamp(),date=str(day)))
    return dict(items=result,source='Aladhan — yöntem '+str(p['method'])+'; hesaplanan vakitler')


def feeds(c,store):
    import feedparser
    sources=[]
    for channel in c['feeds']['youtube']:
        ident=channel['id'] if isinstance(channel,dict) else channel
        if not re.fullmatch(r'UC[\w-]{22}',ident):raise ValueError('YouTube UC kanal kimliği gerekli')
        sources.append(('youtube:'+ident,channel.get('name',ident) if isinstance(channel,dict) else ident,'https://www.youtube.com/feeds/videos.xml?channel_id='+ident,'youtube'))
    for sub in c['feeds']['subreddits']:
        if not re.fullmatch(r'[A-Za-z0-9_]{1,40}',sub):raise ValueError('Subreddit adı')
        sources.append(('reddit:'+sub,'r/'+sub,'https://www.reddit.com/r/'+sub+'/new/.rss','reddit'))
    for kind in ('news','podcasts'):
        for source in c['feeds'][kind]:sources.append((kind+':'+hashlib.sha256(source['url'].encode()).hexdigest()[:16],source['name'],safe_url(source['url']),kind))
    if not sources:raise NeedsConfig('YouTube, subreddit, haber veya podcast kaynağı ekle')
    result=[]
    for source,name,url,kind in sources[:60]:
        try:
            f=feedparser.parse(http(url));entries=[]
            if f.get('bozo') and not f.entries:raise ValueError('RSS çözümlenemedi')
            for e in f.entries[:50]:
                item=dict(id=str(e.get('id',e.get('link',e.get('title','')))),title=e.get('title','Başlıksız'),url=e.get('link',''),date=e.get('published',e.get('updated','')))
                enclosure=next((l.get('href') for l in e.get('links',[]) if l.get('rel')=='enclosure'),None)
                if enclosure:item['audio']=enclosure
                entries.append(item)
            count,fresh=store.feed(source,entries)
            result.append(dict(id=source,name=name,kind=kind,status='ready',count=count,items=entries[:10],new=fresh[:3]))
        except Exception as e:result.append(dict(id=source,name=name,kind=kind,status='error',error=type(e).__name__,count=None,items=[]))
    return dict(sources=result)


def reddit(c,store):
    keys={k:os.environ.get('KINGDOM_REDDIT_'+k.upper()) for k in ('client_id','client_secret','refresh_token')}
    if not all(keys.values()):raise NeedsConfig('Reddit OAuth client_id/client_secret/refresh_token gerekli')
    import praw
    r=praw.Reddit(**keys,user_agent='linux:FatihKingdom:1.0 (personal desktop)',requestor_kwargs={'timeout':12})
    me=r.user.me()
    unread=list(r.inbox.unread(limit=1000))
    saved=[]
    for e in me.saved(limit=30):saved.append(dict(id=e.fullname,title=getattr(e,'title',getattr(e,'body',''))[:180],url='https://www.reddit.com'+e.permalink))
    return dict(username=str(me),karma=me.link_karma+me.comment_karma,unread=len(unread),capped=len(unread)==1000,saved=saved)


def mail(c,store):
    p=c['imap'];password=os.environ.get('KINGDOM_IMAP_PASSWORD');token=os.environ.get('KINGDOM_IMAP_ACCESS_TOKEN')
    if not p['user'] or not (password or token):raise NeedsConfig('IMAP kullanıcı + uygulama şifresi veya OAuth erişim belirteci gerekli')
    with imaplib.IMAP4_SSL(p['host'],int(p.get('port',993)),timeout=12) as m:
        if token:
            auth=('user='+p['user']+'\x01auth=Bearer '+token+'\x01\x01').encode()
            m.authenticate('XOAUTH2',lambda _:auth)
        else:m.login(p['user'],password)
        status,_=m.select(p.get('folder','INBOX'),readonly=True)
        if status!='OK':raise ValueError('IMAP klasörü açılamadı')
        status,data=m.search(None,'UNSEEN')
        if status!='OK':raise ValueError('IMAP sayımı başarısız')
        return dict(unread=len(data[0].split()),user=p['user'],folder=p.get('folder','INBOX'))


def github(c,store):
    token=os.environ.get('KINGDOM_GITHUB_TOKEN')
    if not token:raise NeedsConfig('GitHub notifications yetkili token gerekli')
    rows=[]
    for page in range(1,11):
        r=get_json('https://api.github.com/notifications?per_page=100&page='+str(page),
           {'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
        rows+=r
        if len(r)<100:break
    return dict(count=len(rows),capped=len(rows)==1000,items=[dict(title=e['subject']['title'],repository=e['repository']['full_name'],url=e['repository']['html_url']) for e in rows[:20]])


def finance(c,store):
    result=[]
    tree=ET.fromstring(http('https://www.tcmb.gov.tr/kurlar/today.xml'))
    for node in tree.findall('Currency'):
        if node.attrib.get('Kod') in ('USD','EUR','GBP'):
            value=float(node.findtext('ForexSelling'));symbol=node.attrib['Kod']+'/TRY'
            result.append(dict(symbol=symbol,value=value,currency='TRY',source='TCMB gösterge satış kuru',date=tree.attrib.get('Tarih'),history=store.history(symbol,value)))
    ids=list(dict.fromkeys(c['finance']['crypto']+['tether-gold']))
    headers={};key=os.environ.get('KINGDOM_COINGECKO_KEY')
    if key:headers['x-cg-demo-api-key']=key
    error=''
    try:crypto=get_json('https://api.coingecko.com/api/v3/simple/price?'+urlencode(dict(ids=','.join(ids),vs_currencies='usd,try',include_last_updated_at='true')),headers)
    except Exception as e:crypto={};error='CoinGecko: '+type(e).__name__
    for ident,e in crypto.items():
        if ident=='tether-gold':symbol='ALTIN / gram (XAUT referansı)';value=e['try']/31.1034768;currency='TRY'
        else:symbol=ident.upper();value=e['usd'];currency='USD'
        result.append(dict(symbol=symbol,value=value,currency=currency,source='CoinGecko; kuyumcu satış fiyatı değildir' if ident=='tether-gold' else 'CoinGecko',timestamp=e.get('last_updated_at'),history=store.history(symbol,value)))
    return dict(items=result,error=error)


def stocks(c,store):
    symbols=c['finance']['stocks']
    if not symbols:raise NeedsConfig('BIST sembollerini ekle; ör. THYAO.IS')
    import yfinance as yf
    result=[]
    for symbol in symbols[:12]:
        ticker=yf.Ticker(symbol);h=ticker.history(period='5d',interval='1h',timeout=12)
        if h.empty:continue
        result.append(dict(symbol=symbol,value=float(h['Close'].iloc[-1]),history=[float(x) for x in h['Close'].tail(48)],timestamp=h.index[-1].timestamp(),source='Yahoo Finance; gecikmeli olabilir'))
    if not result:raise ValueError('Hisse fiyatı alınamadı')
    return dict(items=result)


def earthquakes(c,store):
    now=dt.datetime.now(dt.timezone.utc)
    p=dict(start= (now-dt.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),end=now.strftime('%Y-%m-%d %H:%M:%S'),minmag=2,orderby='timedesc',limit=30)
    data=get_json('https://deprem.afad.gov.tr/apiv2/event/filter?'+urlencode(p))
    return dict(items=[dict(id=e.get('eventID'),title=e.get('location',e.get('title','')),magnitude=float(e['magnitude']),time=e.get('date'),latitude=e.get('latitude'),longitude=e.get('longitude'),url='https://deprem.afad.gov.tr/last-earthquakes.html') for e in data],source='AFAD')


def twitch(c,store):
    channels=c['twitch']['channels'];cid=os.environ.get('KINGDOM_TWITCH_CLIENT_ID');secret=os.environ.get('KINGDOM_TWITCH_CLIENT_SECRET')
    if not channels or not cid or not secret:raise NeedsConfig('Twitch kanal listesi + client_id/client_secret gerekli')
    from twitchAPI.twitch import Twitch
    async def fetch():
        t=await Twitch(cid,secret)
        try:return [dict(name=e.user_name,title=e.title,viewers=e.viewer_count,url='https://twitch.tv/'+e.user_login) async for e in t.get_streams(user_login=channels[:100])]
        finally:await t.close()
    return dict(items=asyncio.run(asyncio.wait_for(fetch(),timeout=25)))


def sports(c,store):
    p=c['sports'];token=os.environ.get('KINGDOM_FOOTBALL_TOKEN')
    if not p['team_id'] or not token:raise NeedsConfig('football-data.org token + takım kimliği gerekli; kapsama sağlayıcıya bağlı')
    rows=get_json('https://api.football-data.org/v4/teams/'+str(int(p['team_id']))+'/matches?status=LIVE',{'X-Auth-Token':token})['matches']
    return dict(items=[dict(title=e['homeTeam']['name']+' — '+e['awayTeam']['name'],score=e['score'].get('fullTime'),status=e['status'],source='football-data.org') for e in rows])


def today(c,store):
    now=dt.datetime.now();r=get_json('https://tr.wikipedia.org/api/rest_v1/feed/onthisday/events/'+now.strftime('%m/%d'))
    words=c['dailyWords'];word=words[now.date().toordinal()%len(words)] if words else None
    phase=((time.time()-947182440)/86400%29.530588853)/29.530588853
    return dict(events=[dict(year=e['year'],text=e['text'],url=e.get('pages',[{}])[0].get('content_urls',{}).get('desktop',{}).get('page','')) for e in r.get('events',[])[:12]],word=word,moonPhase=round(phase,3),moonSource='Yaklaşık sinodik ay hesabı')


def calendars(c,store):
    from icalendar import Calendar
    import recurring_ical_events
    p=c['calendar'];data=[]
    for path in p['files']:data.append(Path(path).expanduser().read_bytes())
    for url in p['urls']:data.append(http(safe_url(url)))
    if not data:raise NeedsConfig('ICS dosyası veya abonelik adresi ekle')
    tz=ZoneInfo(c['location']['timezone']);now=dt.datetime.now(tz);rows=[]
    for raw in data:
        cal=Calendar.from_ical(raw)
        for e in recurring_ical_events.of(cal).between(now-dt.timedelta(days=1),now+dt.timedelta(days=7)):
            start=e.decoded('dtstart')
            if not isinstance(start,dt.datetime):start=dt.datetime.combine(start,dt.time(),tz)
            elif start.tzinfo is None:start=start.replace(tzinfo=tz)
            rows.append(dict(id=str(e.get('uid',''))+str(start.timestamp()),title=str(e.get('summary','Etkinlik')),timestamp=start.timestamp(),time=start.astimezone(tz).strftime('%d.%m %H:%M')))
    return dict(items=sorted(rows,key=lambda x:x['timestamp']))


def media(c,store):
    sep='\x1f'
    fmt=sep.join(['{{playerName}}','{{title}}','{{artist}}','{{album}}','{{mpris:artUrl}}','{{mpris:length}}','{{status}}','{{position}}'])
    try:output=run(['playerctl','-a','metadata','--format',fmt])
    except RuntimeError:return dict(players=[],current=None)
    rows=[]
    for line in output.splitlines():
        fields=line.split(sep)
        if len(fields)!=8:continue
        player,title,artist,album,art,length,status,position=fields
        def seconds(v):
            try:return float(v)/1e6
            except ValueError:return 0
        cover=''
        if art.startswith(('https://','http://')):
            target=STATE/'covers'/(hashlib.sha256(art.encode()).hexdigest()+'.img');target.parent.mkdir(exist_ok=True)
            try:
                if not target.exists():target.write_bytes(http(art,limit=6*1024*1024))
                cover=str(target)
                files=sorted(target.parent.glob('*.img'),key=lambda f:f.stat().st_mtime,reverse=True)
                for old in files[80:]:old.unlink(missing_ok=True)
            except Exception:pass
        elif art.startswith('file://'):cover=__import__('urllib.parse',fromlist=['unquote']).unquote(__import__('urllib.parse',fromlist=['urlparse']).urlparse(art).path)
        rows.append(dict(player=player,title=title,artist=artist,album=album,art=Path(cover).as_uri() if cover else '',cover=cover,status=status,position=seconds(position),length=seconds(length)))
    rows.sort(key=lambda x:x['status']!='Playing')
    return dict(players=rows,current=rows[0] if rows else None)


def hardware(c,store):
    def number(p):
        try:return float(Path(p).read_text().strip())
        except (OSError,ValueError):return None
    temperatures=[];fans=[];batteries=[]
    for d in Path('/sys/class/hwmon').glob('*'):
        try:name=(d/'name').read_text().strip()
        except OSError:continue
        for p in d.glob('temp*_input'):
            value=number(p)
            if value is not None:temperatures.append(dict(name=name,value=value/1000))
        for p in d.glob('fan*_input'):
            value=number(p)
            if value is not None:fans.append(dict(name=name,value=value))
    for d in Path('/sys/class/power_supply').glob('*'):
        try:
            if (d/'type').read_text().strip()!='Battery':continue
            status=(d/'status').read_text().strip();full=number(d/'energy_full');design=number(d/'energy_full_design');energy=number(d/'energy_now');power=number(d/'power_now')
            estimate=((full-energy) if status=='Charging' else energy)/power*3600 if full is not None and energy is not None and power and power>0 else None
            health=100*full/design if full is not None and design else None
            if health is None:
                full=number(d/'charge_full');design=number(d/'charge_full_design');health=100*full/design if full is not None and design else None
            batteries.append(dict(name=d.name,percent=number(d/'capacity'),health=health,status=status,estimate=estimate))
        except OSError:continue
    disks=[]
    for path in ('/','/home'):
        u=shutil.disk_usage(path);disks.append(dict(path=path,percent=100*u.used/u.total,free=u.free))
    return dict(temperatures=temperatures,fans=fans,batteries=batteries,disks=disks,load=os.getloadavg(),source='sysfs / disk_usage')


def bluetooth(c,store):
    async def fetch():
        from dbus_next.aio import MessageBus
        from dbus_next import BusType
        bus=await MessageBus(bus_type=BusType.SYSTEM).connect()
        try:
            intro=await bus.introspect('org.bluez','/')
            obj=bus.get_proxy_object('org.bluez','/',intro)
            rows=await obj.get_interface('org.freedesktop.DBus.ObjectManager').call_get_managed_objects()
            result=[]
            for path,interfaces in rows.items():
                device=interfaces.get('org.bluez.Device1',{})
                if not device or not device.get('Connected') or not device['Connected'].value:continue
                battery=interfaces.get('org.bluez.Battery1',{}).get('Percentage')
                name=device.get('Alias',device.get('Name'))
                result.append(dict(name=name.value if name else 'Bluetooth',battery=battery.value if battery else None))
            return dict(items=result)
        finally:bus.disconnect()
    return asyncio.run(asyncio.wait_for(fetch(),timeout=8))


def queue(c,store):
    import socket
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(2)
        try:s.connect(str(RUNTIME/'mpv.sock'))
        except OSError:return dict(upcoming=[],playlist=[])
        s.sendall(b'{"command":["get_property","playlist"],"request_id":83}\n')
        with s.makefile() as reader:
            for line in reader:
                obj=json.loads(line)
                if obj.get('request_id')==83:break
    items=obj.get('data') or []
    index=next((i for i,e in enumerate(items) if e.get('current')),len(items))
    known={e['url']:e for e in __import__('common').load(STATE/'local.json').get('queue',[])}
    upcoming=[dict(title=known.get(e.get('filename'),{}).get('title',e.get('title') or e.get('filename','')),url=e.get('filename','')) for e in items[index+1:index+4]]
    return dict(upcoming=upcoming,playlist=items)


PROVIDERS={
 'queue':(4,queue),
 'media':(4,media), 'hardware':(10,hardware), 'bluetooth':(60,bluetooth),
 'feeds':(900,feeds), 'weather':(1200,weather), 'aqi':(1800,aqi),
 'prayer':(3600,prayer), 'reddit':(300,reddit), 'mail':(180,mail),
 'github':(300,github), 'finance':(600,finance), 'stocks':(900,stocks),
 'earthquakes':(300,earthquakes), 'twitch':(180,twitch), 'sports':(120,sports),
 'today':(3600,today), 'calendar':(900,calendars)
}
