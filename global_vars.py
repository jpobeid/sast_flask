import os

PATH_DATABASE = os.path.join('assets', 'database.db')
PATH_AUTHORIZED_EMAILS = os.path.join('assets', 'authorized_emails.csv')

PATH_INPUTS = os.path.join('data', 'inputs')
PATH_OUTPUTS = os.path.join('data', 'outputs')

name_output_file = 'ContouredByAI.dcm'
name_dir_head_neck = 'head_neck'

path_main = os.getcwd()

str_page_upload = 'upload'
str_base64_key = 'base64code'

json_failure = {'success': False}
json_success = {'success': True}
