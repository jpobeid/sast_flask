import os
import json

PASS_VAR = json.loads(os.environ.get('PASS_VAR'))

print(PASS_VAR['email']['user'])