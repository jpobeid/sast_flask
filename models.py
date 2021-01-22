import os
import numpy as np

from flask_restful import fields
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db():
    if not np.any([e.split('.')[-1] == 'db' for e in os.listdir()]):
        db.create_all()
        print('Initialized database')


class UserModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50))
    token = db.Column(db.Integer)
    salt_exp = db.Column(db.Integer)
    password = db.Column(db.String(100))

    resource_fields = {
        'id': fields.Integer,
        'email': fields.String,
        'token': fields.Integer,
        'salt_exp': fields.Integer,
        'password': fields.String,
    }

    def __init__(self, email, token, salt_exp, password):
        self.email = email
        self.token = token
        self.salt_exp = salt_exp
        self.password = password
