import os
import shutil
import pandas as pd

from flask import request
from flask_restful import Resource
from models import db, UserModel

from num_generator import NumGen
import email_sender
import global_vars as var
from img_analysis import DicomImage
from algorithms.head_neck import main as main_head_neck


class TestResource(Resource):
    def get(self):
        return var.json_success


class UserResource(Resource):
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
                    str_salt_hashed_pass = NumGen.get_salt_hashed_password(
                        str_received_hashed_pass, user.token, user.salt_exp)
                    is_password_correct = str_salt_hashed_pass == user.password
                    if is_password_correct:
                        return {'token': str(user.token), 'pin': NumGen.get_user_pin(user.token)}, 200
                    else:
                        return var.json_failure, 401
                else:
                    return var.json_failure, 404
            else:
                return var.json_failure, 404
        elif str_page == 'register':
            if n_phase == 0:
                # Receive posted variables
                str_received_email = request.json['email']

                # Check authorized && available (not already registered) emails
                df_email_auth = pd.read_csv(
                    'authorized_emails.csv', header=None)
                is_email_authorized = df_email_auth[0].str.fullmatch(
                    str_received_email).any()
                is_email_available = UserModel.query.filter_by(
                    email=str_received_email).first() is None

                if is_email_authorized and is_email_available:
                    generated_token = NumGen.get_token()
                    generated_salt_exp = NumGen.get_salt_exp()
                    email_sender.send_email(
                        str_received_email, generated_token, None)

                    # Make new user and commit to DB
                    new_user = UserModel(str_received_email,
                                         generated_token, generated_salt_exp, None)
                    db.session.add(new_user)
                    db.session.commit()

                    return var.json_success, 200
                elif not is_email_authorized:
                    return var.json_failure, 401
                else:
                    return var.json_failure, 409
            elif n_phase == 1:
                # Receive posted variables
                str_received_email = request.json['email']
                str_received_token = request.json['token']

                # Cross reference against recently generated and stored token
                user_stored_token = UserModel.query.filter_by(
                    email=str_received_email).first().token

                if str_received_token == str(user_stored_token):
                    return var.json_success, 200
                else:
                    return var.json_failure, 401
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
                return var.json_failure, 404


class DashResource(Resource):
    def get(self, str_page, n_index):
        if str_page == 'process':
            user_email = request.headers['email']
            if n_index == 0:
                #Head & Neck
                # main_head_neck.main(user_email)
                email_sender.send_email(
                    user_email, None, os.path.join(var.name_dir_output, user_email, var.name_output_file))
                print(f'Email sent to: {user_email}')
                shutil.rmtree(os.path.join(var.name_dir_output, user_email))
                return var.json_success, 200
            else:
                return var.json_failure, 400
        elif str_page == 'image':
            user_email = request.headers['email']
            code = DicomImage.get_random_image_base64text(user_email)
            return {var.str_base64_key: code}, 200
        else:
            return var.json_failure, 400

    def post(self, str_page, n_index):
        if str_page == var.str_page_upload:
            user_email = request.form['email']
            user_token = request.form['token']
            user_pin = request.form['pin']
            is_authenticated = user_pin == NumGen.get_user_pin(user_token)
            if is_authenticated:
                path_input = os.path.join(var.path_main, var.name_dir_input)
                path_upload = os.path.join(path_input, user_email)
                if not os.path.exists(path_upload):
                    os.mkdir(path_upload)
                file_uploaded = request.files['fileDicom']
                file_uploaded.save(path_upload + f'/CT_{n_index}.dcm')
                return var.json_success, 200
            else:
                return var.json_failure, 403
        else:
            return var.json_failure, 400
