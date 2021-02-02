import global_vars as var
import numpy as np
import hashlib

class NumGen():

    @staticmethod
    def get_token():
        n_min = 1e5
        return np.random.randint(low=n_min, high=n_min*10)

    @staticmethod
    def get_salt_exp():
        n_min = 1e1
        salt_exp = np.random.randint(low=n_min, high=n_min*10)
        return salt_exp
    
    @staticmethod
    def get_salt_hashed_password(hashed_pass, token, salt_exp):
        salt = token ** salt_exp
        str_combination = hashed_pass + str(salt)
        salt_hashed_password = hashlib.sha256(str_combination.encode('utf8')).hexdigest()
        return salt_hashed_password

    @staticmethod
    def get_user_pin(token):
        salt = var.test_secret_key
        str_combination = str(token) + salt
        salt_hashed_pin = hashlib.sha256(str_combination.encode('utf8')).hexdigest()
        return salt_hashed_pin