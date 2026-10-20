"""Qtile main-loop bridge: bounded local socket, layouts and undo without eval."""
import collections,json,os,socket,stat,time,subprocess
from pathlib import Path
from libqtile import hook,qtile
from libqtile.config import Key
from libqtile.lazy import lazy


ACTIONS={'home':'space','overview':'w','undo':'z','annotate':'a','magnify':'g','color':'c','snippets':'t','presentation':'F9','palette':'p','radial':'r','drop':'f','ocr':'x','recording':'v'}
def settings():
    path=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'violet-desktop/settings.json'
    try:return json.loads(path.read_text())
    except (OSError,ValueError):return {}
def bindings(values,mod='mod4'):
    if not isinstance(values,dict) or set(values)-set(ACTIONS):raise ValueError('Kısayol işlemi geçersiz')
    out=[];seen=set()
    for action,key in ACTIONS.items():
        row=values.get(action,{'mods':[mod,'mod1'],'key':key});mods=row.get('mods',[]);name=row.get('key','')
        if not isinstance(mods,list) or not mods or any(m not in ('mod4','mod1','control','shift','mod2','mod3','mod5') for m in mods) or len(set(mods))!=len(mods):raise ValueError('Kısayol değiştiricileri geçersiz')
        if not isinstance(name,str) or not name or len(name)>40 or any(c.isspace() for c in name):raise ValueError('Kısayol tuşu geçersiz')
        ident=(tuple(sorted(mods)),name.lower())
        if ident in seen:raise ValueError('Kısayollar birbirleriyle çakışıyor')
        seen.add(ident);args=['violet-desktop']+([] if action=='home' else [action]);binding=Key(mods,name,lazy.spawn(args),desc='Violet · '+action);binding._violet_suite_owned=True;binding._violet_action=action;out.append(binding)
    return out

class Bridge:
    name='Violet timed inhibitor'
    def __init__(self,q):
        self.q=q;self.closed=False;self.peers={};self.history=collections.deque(maxlen=32);self.last=None;self.awaiting=[];self.timer=None
        root=Path(os.environ.get('XDG_RUNTIME_DIR','/run/user/'+str(os.getuid())))/'violet-desktop';root.mkdir(mode=0o700,exist_ok=True)
        if root.is_symlink() or root.stat().st_uid!=os.getuid():raise ValueError('Qtile IPC dizini geçersiz')
        os.chmod(root,0o700);self.path=root/'qtile.sock'
        if self.path.exists():
            if not stat.S_ISSOCK(self.path.lstat().st_mode) or self.path.lstat().st_uid!=os.getuid():raise ValueError('Qtile IPC yolu geçersiz')
            self.path.unlink()
        self.server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);self.server.bind(str(self.path));os.chmod(self.path,0o600);self.server.listen(16);self.server.setblocking(False)
        self.tick()
    def scratch(self,g):return g.name=="scratchpad" or hasattr(g,"_dropdownconfig")
    def clients(self,layout):
        if hasattr(layout,"get_windows"):return layout.get_windows()
        return getattr(getattr(layout,"clients",None),"clients",[])
    def windows(self):
        return {wid:w for wid,w in self.q.windows_map.items() if getattr(w,'group',None) and not self.scratch(w.group) and not str(getattr(w,'name','')).startswith('Violet ·')}
    def snapshot(self):
        groups=[]
        for g in self.q.groups:
            if self.scratch(g):continue
            clients=self.clients(g.layout)
            groups.append({'name':g.name,'layout':g.layout.name,'ratio':getattr(g.layout,'ratio',None),'order':[w.wid for w in clients]})
        windows=[]
        for wid,w in self.windows().items():
            info=w.info();info.update({'id':wid,'group':w.group.name,'floating':bool(w.floating),'fullscreen':bool(w.fullscreen),'minimized':bool(w.minimized),'classes':w.get_wm_class() or []});windows.append(info)
        return {'groups':groups,'windows':sorted(windows,key=lambda w:w['id']),'current':self.q.current_group.name,'layouts':list(dict.fromkeys(l.name for l in self.q.current_group.layouts)),'screen':{'x':self.q.current_screen.dx,'y':self.q.current_screen.dy,'width':self.q.current_screen.dwidth,'height':self.q.current_screen.dheight}}
    def signature(self,state):
        return json.dumps({'groups':state['groups'],'windows':[{k:w.get(k) for k in ('id','group','x','y','width','height','floating','fullscreen','minimized')} for w in state['windows']]},sort_keys=True)
    def record(self):
        now=self.snapshot()
        if self.last and self.signature(self.last)!=self.signature(now):self.history.append(self.last)
        self.last=now
    def restore(self,state):
        windows=self.windows()
        for row in state['groups']:
            g=self.q.groups_map.get(row['name'])
            if not g:continue
            if row['layout'] in [l.name for l in g.layouts]:g.setlayout(row['layout'])
            if row.get('ratio') is not None and hasattr(g.layout,'set_ratio'):g.layout.set_ratio(row['ratio'])
        for row in state['windows']:
            w=windows.get(row['id'])
            if not w or row['group'] not in self.q.groups_map:continue
            w.fullscreen=False;w.minimized=False
            if w.group.name!=row['group']:w.togroup(row['group'])
            w.floating=row['floating']
            if row['floating']:w.set_size_floating(row['width'],row['height']);w.set_position_floating(row['x'],row['y'])
            w.fullscreen=row['fullscreen'];w.minimized=row['minimized']
        # Layouts that expose swap can restore their client order as well.
        for row in state['groups']:
            g=self.q.groups_map.get(row['name']);layout=getattr(g,'layout',None)
            clients=self.clients(layout)
            if not clients or not hasattr(layout,'swap'):continue
            desired=[wid for wid in row['order'] if wid in windows and windows[wid] in clients]
            for i,wid in enumerate(desired):
                if i<len(clients) and clients[i].wid!=wid:layout.swap(clients[i],windows[wid])
            g.layout_all()
        if state['current'] in self.q.groups_map:self.q.groups_map[state['current']].toscreen()
        self.last=self.snapshot()
    def preset(self,request):
        template=request.get('template','split');group=request.get('group') or self.q.current_group.name
        if template not in ('split','three','reading','presentation','tile'):raise ValueError('Düzen şablonu geçersiz')
        if group not in self.q.groups_map or self.scratch(self.q.groups_map[group]):raise ValueError('Çalışma alanı geçersiz')
        g=self.q.groups_map[group];wins=self.windows();ids=request.get('ids') or [w.wid for w in g.windows if w.wid in wins]
        if not isinstance(ids,list) or len(ids)>30:raise ValueError('Pencere listesi geçersiz')
        chosen=[wins[i] for i in ids if i in wins]
        if not chosen:raise ValueError('Önce uygulama pencerelerini aç veya seç')
        self.record();self.history.append(self.snapshot());g.toscreen()
        s=self.q.current_screen;x,y,width,height=s.dx,s.dy,s.dwidth,s.dheight;gap=12
        for i,w in enumerate(chosen):
            if w.group!=g:w.togroup(group)
            w.minimized=False;w.fullscreen=False
            if template=='tile':w.floating=False;continue
            if template=='presentation':
                if i==0:w.fullscreen=True
                continue
            cols=3 if template=='three' else 2;ratio=.63 if template=='reading' else .5
            if cols==2 and i==0:rect=(x+gap,y+gap,int(width*ratio)-gap*2,height-gap*2)
            elif cols==2:
                n=max(1,len(chosen)-1);rh=(height-gap*(n+1))//n;rect=(x+int(width*ratio)+gap,y+gap+(i-1)*(rh+gap),int(width*(1-ratio))-gap*2,rh)
            else:
                n=(len(chosen)+2)//3;cw=(width-gap*4)//3;rh=(height-gap*(n+1))//n;rect=(x+gap+(i%3)*(cw+gap),y+gap+(i//3)*(rh+gap),cw,rh)
            w.floating=True;w.set_size_floating(max(120,rect[2]),max(100,rect[3]));w.set_position_floating(rect[0],rect[1])
        self.last=self.snapshot();return 'Düzen uygulandı'
    def dispatch(self,r):
        action=r.get('action');wins=self.windows()
        if action=='global-awake':
            manager=self.q.core.idle_inhibitor_manager
            from libqtile.backend.base.idle_inhibit import Inhibitor,InhibitorType
            if r.get('enabled'):
                owned=manager._convert_inhibitor(Inhibitor(self.q,window=self,inhibitor_type=InhibitorType.GLOBAL))
                manager.add_inhibitor_safe(owned)
            else:manager.remove_inhibitor(lambda item:getattr(item,'window',None) is self)
            return 'Qtile uyku engelleyicisi güncellendi'
        if action in ('pen-menu','pen-secondary'):
            choice='radial' if action=='pen-menu' else settings().get('penSecondary','eraser')
            allowed={'radial','annotate','eraser','quick-note','palette','mybrain','none'}
            if choice not in allowed:raise ValueError('Kalem işlemi geçersiz')
            if choice=='mybrain':self.q.spawn(['mybrain-python'])
            elif choice!='none':self.q.spawn(['violet-desktop',choice])
            return 'Kalem işlemi: '+choice
        if action=='screen-groups':
            groups=r.get('groups',[])
            if not isinstance(groups,list) or len(groups)>len(self.q.screens) or len(set(groups))!=len(groups) or any(g not in self.q.groups_map or self.scratch(self.q.groups_map[g]) for g in groups):raise ValueError('Ekran / alan eşlemesi geçersiz')
            for i,g in enumerate(groups):self.q.groups_map[g].toscreen(i)
            return 'Çalışma alanları ekranlara yerleştirildi'
        if action=='session':
            entries=r.get('entries',[])
            if not isinstance(entries,list) or not 0<len(entries)<=20:raise ValueError('1–20 uygulamalı oturum gerekli')
            for e in entries:
                if e['group'] not in self.q.groups_map or self.scratch(self.q.groups_map[e['group']]):raise ValueError('Çalışma alanı bulunamadı')
                if not isinstance(e.get('classes'),list) or not e['classes'] or any(not isinstance(c,str) or len(c)>200 for c in e['classes']):raise ValueError('Pencere sınıfları geçersiz')
                args=e.get('argv')
                if not isinstance(args,list) or not 0<len(args)<=64 or any(not isinstance(a,str) or '\0' in a or len(a)>4096 for a in args):raise ValueError('Uygulama komutu geçersiz')
            reused=set()
            for e in entries:
                found=next((w for w in wins.values() if w.wid not in reused and set(e['classes']) & set(w.get_wm_class() or [])),None)
                if found:found.togroup(e['group']);found.minimized=False;reused.add(found.wid)
                else:self.awaiting.append({**e,'until':time.monotonic()+60});self.q.spawn(e['argv'],group=e['group'])
            self.q.groups_map[entries[0]['group']].toscreen();return 'Oturum açıldı; yeni pencereler 60 saniye eşleştirilecek'
        if action=='shortcuts':return self.rebind(r.get('bindings',{}))
        if action=='pointer':
            x,y=self.q.core.get_mouse_position()
            screens=[{'x':s.x,'y':s.y,'width':s.width,'height':s.height} for s in self.q.screens]
            return {'x':x,'y':y,'screens':screens}
        if action=='state':return {**self.snapshot(),'undo':len(self.history)}
        if action=='undo':
            self.record()
            if not self.history:raise ValueError('Geri alınacak düzen yok')
            self.restore(self.history.pop());return 'Önceki düzen geri getirildi'
        if action=='preset':return self.preset(r)
        if action=='saved-preset':
            roles=r.get('roles',[]);ids=[]
            for role in roles:
                found=next((wid for wid,w in wins.items() if wid not in ids and set(role.get('classes',[])) & set(w.get_wm_class() or [])),None)
                if found is not None:ids.append(found)
            if not ids:raise ValueError('Kaydedilmiş düzene ait uygulamalar açık değil')
            return self.preset({**r,'ids':ids})
        if action=='move':
            w=wins.get(int(r['id']));target=r.get('group')
            if not w or target not in self.q.groups_map or self.scratch(self.q.groups_map[target]):raise ValueError('Pencere/alan bulunamadı')
            self.history.append(self.snapshot());w.togroup(target);self.last=self.snapshot();return 'Pencere taşındı'
        if action=='focus':
            w=wins.get(int(r['id']))
            if not w:raise ValueError('Pencere kapandı')
            w.group.toscreen();w.minimized=False;w.group.focus(w,warp=False);return 'Pencere seçildi'
        if action=='layout':
            g=self.q.groups_map.get(r.get('group') or self.q.current_group.name)
            if not g or r.get('name') not in [l.name for l in g.layouts]:raise ValueError('Düzen bu alanda mevcut değil')
            self.history.append(self.snapshot());g.setlayout(r['name']);self.last=self.snapshot();return 'Düzen değişti'
        if action=='awake-window':
            w=wins.get(int(r['id']))
            if not w:raise ValueError('Pencere bulunamadı')
            if not hasattr(w,'add_idle_inhibitor'):raise ValueError('Bu Qtile sürümünde pencere uyku engelleyicisi yok')
            w.add_idle_inhibitor() if r.get('enabled',True) else w.remove_idle_inhibitor();return 'Pencere uyku engelleyicisi güncellendi'
        raise ValueError('Bilinmeyen Qtile işlemi')
    def rebind(self,values):
        replacement=bindings(values,getattr(self.q.config,'mod','mod4'));old=[k for k in self.q.config.keys if getattr(k,'_violet_suite_owned',False)];others=[k for k in self.q.config.keys if not getattr(k,'_violet_suite_owned',False)]
        occupied={(tuple(sorted(k.modifiers)),k.key.lower()) for k in others}
        if any((tuple(sorted(k.modifiers)),k.key.lower()) in occupied for k in replacement):raise ValueError('Mevcut Qtile kısayoluyla çakışıyor')
        # Validate names before altering grabs, using Qtile's backend name conversion.
        from libqtile.backend.wayland.core import translate_masks,lib
        for k in replacement:
            translate_masks(k.modifiers)
            if not lib.qwu_keysym_from_name(k.key.encode()):raise ValueError('Tuş adı bulunamadı: '+k.key)
        try:
            for k in old:self.q.ungrab_key(k)
            for k in replacement:self.q.grab_key(k)
        except Exception:
            for k in replacement:
                try:self.q.ungrab_key(k)
                except Exception:pass
            for k in old:self.q.grab_key(k)
            raise
        self.q.config.keys[:]=others+replacement;return 'Kısayollar uygulandı'
    def tick(self):
        if self.closed:return
        for _ in range(16):
            try:peer,_=self.server.accept();peer.setblocking(False);self.peers[peer]=[b'',time.monotonic()]
            except BlockingIOError:break
        for peer,(buf,started) in list(self.peers.items()):
            try:
                try:data=peer.recv(65536)
                except BlockingIOError:
                    if time.monotonic()-started>3:raise ValueError('IPC zaman aşımı')
                    continue
                if not data:raise ValueError('Bağlantı kapandı')
                buf+=data;self.peers[peer][0]=buf
                if len(buf)>65536:raise ValueError('İstek fazla büyük')
                if b'\n' not in buf:continue
                try:result={'ok':True,'data':self.dispatch(json.loads(buf.split(b'\n',1)[0]))}
                except Exception as e:result={'ok':False,'error':str(e)}
                peer.sendall((json.dumps(result,default=str)+'\n').encode());peer.close();del self.peers[peer]
            except (ValueError,OSError):peer.close();self.peers.pop(peer,None)
        value=settings().get('penButton',331);os.environ['VIOLET_PEN_MENU_BUTTON']=str(value if value in (331,332) else 0)
        os.environ['VIOLET_PEN_SECONDARY_ENABLED']='1' if settings().get('penSecondary','eraser')!='none' else '0'
        self.awaiting=[r for r in self.awaiting if r['until']>time.monotonic()]
        try:self.record()
        except Exception:pass
        self.timer=self.q.call_later(.25,self.tick)
    def stop(self):
        self.closed=True
        if self.timer:self.timer.cancel()
        for p in self.peers:p.close()
        try:self.q.core.idle_inhibitor_manager.remove_inhibitor(lambda item:getattr(item,'window',None) is self)
        except Exception:pass
        self.server.close();self.path.unlink(missing_ok=True)

@hook.subscribe.client_managed
def float_desktop_tools(window):
    bridge=getattr(qtile,'_violet_desktop_bridge',None)
    if bridge:
        for row in list(bridge.awaiting):
            if set(row['classes']) & set(window.get_wm_class() or []):window.togroup(row['group']);bridge.awaiting.remove(row);break
    if str(getattr(window,'name','')).startswith('Violet ·'):
        window.floating=True;window.center()

@hook.subscribe.startup_complete
def start():
    previous=getattr(qtile,'_violet_desktop_bridge',None)
    if previous:previous.stop()
    qtile._violet_desktop_bridge=Bridge(qtile)

@hook.subscribe.shutdown
def stop():
    bridge=getattr(qtile,'_violet_desktop_bridge',None)
    if bridge:bridge.stop()
    subprocess.Popen(['systemctl','--user','stop','violet-desktop.service','violet-kdeconnect.service'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def install(config):
    keys=config['keys'];mod=config.get('mod','mod4');keys[:]=[k for k in keys if not getattr(k,'_violet_suite_owned',False)]
    taken={(tuple(sorted(k.modifiers)),k.key.lower()) for k in keys}
    for binding in bindings(settings().get('shortcuts',{}),mod):
        if (tuple(sorted(binding.modifiers)),binding.key.lower()) in taken:continue
        keys.append(binding)
