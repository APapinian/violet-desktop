import json,time
from common import STATE,read,config
previous=None
while True:
    state=read(STATE/'status.json',{});value={'presentation':bool(state.get('presentation')),'awake':bool(state.get('awake')),'recording':bool(state.get('recorder',{}).get('active')),'ui':{k:config()[k] for k in ('dockPins','panelOrder','motionSpeed')}}
    line=json.dumps(value)
    if line!=previous:print(line,flush=True);previous=line
    time.sleep(1)
