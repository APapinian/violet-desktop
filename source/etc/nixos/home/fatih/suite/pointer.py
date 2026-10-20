import json
from common import request
print(json.dumps(request('qtile','pointer')))
