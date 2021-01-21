import os

from flask import Flask, request
from flask_restful import Api, Resource, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from num_generator import NumGen
import email_sender
import numpy as np
import pandas as pd

app = Flask(__name__)
cors = CORS(app)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


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


init_db()


class UserResource(Resource):
    @marshal_with(UserModel.resource_fields)
    def get(self, str_page, n_phase):
        print(n_phase)
        result = UserModel.query.all()
        return result

    def post(self, str_page, n_phase):
        if str_page == 'login':
            # Receive vars
            str_received_email = request.json['email']
            str_received_hashed_pass = request.json['hashedPass']

            # Check presence of active email/password and correct password
            user = UserModel.query.filter_by(
                    email=str_received_email).first()
            is_email_registered = user is not None
            if is_email_registered:
                is_password_registered = user.password is not None
                if is_password_registered:
                    str_salt_hashed_pass = NumGen.get_salt_hashed_password(str_received_hashed_pass, user.token, user.salt_exp)
                    is_password_correct = str_salt_hashed_pass == user.password
                    if is_password_correct:
                        return {'success': True}, 200
                    else:
                        return {'success': False}, 401
                else:
                    return {'success': False}, 404
            else:
                return {'success': False}, 404
        elif str_page == 'register':
            if n_phase == 0:
                # Receive posted variables
                str_received_email = request.json['email']

                # Check authorized && available (not already registered) emails
                df_email_auth = pd.read_csv('authorized_emails.csv', header=None)
                is_email_authorized = df_email_auth[0].str.fullmatch(
                    str_received_email).any()
                is_email_available = UserModel.query.filter_by(
                    email=str_received_email).first() is None

                if is_email_authorized and is_email_available:
                    generated_token = NumGen.get_token()
                    generated_salt_exp = NumGen.get_salt_exp()
                    email_sender.send_email(str_received_email, generated_token)

                    # Make new user and commit to DB
                    new_user = UserModel(str_received_email,
                                        generated_token, generated_salt_exp, None)
                    db.session.add(new_user)
                    db.session.commit()

                    return {'success': True}, 200
                elif not is_email_authorized:
                    return {'success': False}, 401
                else:
                    return {'success': False}, 409
            elif n_phase == 1:
                # Receive posted variables
                str_received_email = request.json['email']
                str_received_token = request.json['token']

                # Cross reference against recently generated and stored token
                user_stored_token = UserModel.query.filter_by(
                    email=str_received_email).first().token

                if str_received_token == str(user_stored_token):
                    return {'success': True}, 200
                else:
                    return {'success': False}, 401
            elif n_phase == 2:
                # Receive posted vars
                str_received_email = request.json['email']
                str_received_hashed_pass = request.json['hashedPass']

                # Pull relevant user data
                user = UserModel.query.filter_by(
                    email=str_received_email).first()
                user_token = user.token
                user_salt_exp = user.salt_exp

                # Generate salt hashed password
                str_password = NumGen.get_salt_hashed_password(
                    str_received_hashed_pass, user_token, user_salt_exp)
                
                # Commit to DB
                user.password = str_password
                db.session.commit()

            else:
                return {'success': False}, 404
        elif str_page == 'upload':
            user_email = request.form['email']
            user_pin = request.form['pin']
            print(user_email)
            print(user_pin)
            file_uploaded = request.files['fileDicom']
            file_uploaded.save(f'uploaded/dicom{n_phase}.dcm')
            return {'success': True}, 200


api.add_resource(UserResource, '/<string:str_page>/<int:n_phase>')

if __name__ == '__main__':
    app.run(debug=True)
