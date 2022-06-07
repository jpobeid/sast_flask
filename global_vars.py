import os

# Relative paths
PATH_DATABASE = os.path.join('assets', 'database.db')
PATH_AUTHORIZED_EMAILS = os.path.join('assets', 'authorized_emails.csv')
PATH_INPUTS = os.path.join('data', 'inputs')
PATH_OUTPUTS = os.path.join('data', 'outputs')

name_output_file = 'ContouredByAI.dcm'
name_dir_head_neck = 'head_neck'

path_main = os.getcwd()

# Constant key names
KEY_BASE64 = 'base64code'

# Basic responses
json_failure = {'success': False}
json_success = {'success': True}
