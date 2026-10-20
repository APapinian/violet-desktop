import json
import sys
import syncedlyrics
print(json.dumps({'lyrics':syncedlyrics.search(sys.argv[1],synced_only=True,providers=['Lrclib']) or ''}))
