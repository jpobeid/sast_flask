import global_vars as var
import numpy as np
import hashlib

def get_random_n(digits):
    n_min = 10**(digits - 1)
    return np.random.randint(low=n_min, high=n_min*10)

def rehash_password(hashed_pass, token, salt_exp):
    salt = token**salt_exp
    combination = hashed_pass + str(salt)
    salt_rehashed_password = hashlib.sha256(combination.encode('utf8')).hexdigest()
    return salt_rehashed_password

def make_user_pin(email, token):
    # Just a random way to create a 'unique' pin per user
    combination = email.split('@')[0] + str(token)
    pin = hashlib.sha256(combination.encode('utf8')).hexdigest()
    return pin