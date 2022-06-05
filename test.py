import os
import global_vars as var
import hashlib

str_weird = 'jobeid123453masdgfd@stanford.edu'.split('@')[0] + '999999'

print(hashlib.sha256(str_weird.encode('utf8')).hexdigest())