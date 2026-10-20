"""One-time migration of the disabled V5 pen default, retaining custom bindings."""
import json,os
from pathlib import Path
root=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'violet-desktop'
root.mkdir(mode=0o700,parents=True,exist_ok=True)
path=root/'settings.json'
data=json.loads(path.read_text()) if path.exists() else {}
if data.get('violetVersion',0)<6:
    if path.exists() and not (root/'settings.before-v6.json').exists():
        (root/'settings.before-v6.json').write_bytes(path.read_bytes());(root/'settings.before-v6.json').chmod(0o600)
    if data.get('penButton',0)==0:data['penButton']=331
    data.setdefault('penSecondary','eraser')
    shortcuts=data.setdefault('shortcuts',{})
    if shortcuts.get('palette')=={'mods':['mod4','mod1'],'key':'slash'}:
        shortcuts['palette']={'mods':['mod4','mod1'],'key':'p'}
    if shortcuts.get('presentation')=={'mods':['mod4','mod1'],'key':'p'}:
        shortcuts['presentation']={'mods':['mod4','mod1'],'key':'F9'}
    data['violetVersion']=6;tmp=root/'.v6-settings.tmp';tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2));tmp.chmod(0o600);tmp.replace(path)
