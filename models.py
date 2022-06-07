import os

from flask_sqlalchemy import SQLAlchemy
import global_vars as var

db = SQLAlchemy()


def init_db():
    if not os.path.exists(var.PATH_DATABASE):
        db.create_all()
        print('Initialized database...')


class UserModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50))
    token = db.Column(db.Integer)
    salt_exp = db.Column(db.Integer)
    password = db.Column(db.String(100))

    def __init__(self, email, token, salt_exp, password):
        self.email = email
        self.token = token
        self.salt_exp = salt_exp
        self.password = password


class SeriesModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(50), unique=True)
    patient_id = db.Column(db.String(20))
    accession_number = db.Column(db.String(20))
    series_number = db.Column(db.String(20))

    def __init__(self, user, patient_id, accession_number, series_number):
        self.user = user
        self.patient_id = patient_id
        self.accession_number = accession_number
        self.series_number = series_number
