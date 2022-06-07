import os

import global_vars as var

def clear_input_directory(user_email):
    path_user_input = os.path.join(var.PATH_INPUTS, user_email)
    for e in os.listdir(path_user_input):
        os.remove(os.path.join(path_user_input, e))