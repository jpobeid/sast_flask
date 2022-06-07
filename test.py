import os
import global_vars as var

path_input_profile = os.path.join(var.PATH_INPUTS, 'jobeid@stanford.edu')
for e in os.listdir(path_input_profile):
    os.remove(os.path.join(path_input_profile, e))