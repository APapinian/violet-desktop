import json
import os
from pathlib import Path
from libqtile import qtile
from libqtile.log_utils import logger

def publish():
    runtime = os.environ.get('XDG_RUNTIME_DIR')
    if not runtime or not qtile.current_screen:
        return
    try:
        target = Path(runtime) / 'fatih-qtile.json'
        temp = target.with_suffix('.tmp')
        data = {
            'session': os.getpid(),
            'active': qtile.current_group.name if qtile.current_group else '1',
            'title': qtile.current_window.name if qtile.current_window else 'Masaüstü',
            'groups': [{'name': g.name, 'label': g.label or g.name,
                        'occupied': bool(g.windows)} for g in qtile.groups],
        }
        temp.write_text(json.dumps(data, ensure_ascii=False))
        os.chmod(temp, 0o600)
        temp.replace(target)
    except Exception:
        logger.exception('Fatih shell state could not be published')
