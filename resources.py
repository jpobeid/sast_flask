import os
import shutil
import pandas as pd

from flask import request
from flask_restful import Resource
from models import db, UserModel

from functions import num_generator as ng, email_sender, img_analysis as img
import global_vars as var
from algorithms.head_neck import main as main_head_neck


class TestResource(Resource):
    def get(self):
        return var.json_success


class UserResource(Resource):
    def post(self, page, phase):
        if page == 'login':
            # Receive posted variables
            received_email = request.json['email']
            received_hashed_pass = request.json['hashedPass']

            # Check presence of active email/password and correct password
            user = UserModel.query.filter_by(
                email=received_email).first()
            is_email_registered = user is not None
            if is_email_registered:
                is_password_registered = user.password is not None
                if is_password_registered:
                    salt_rehashed_pass = ng.rehash_password(
                        received_hashed_pass, user.token, user.salt_exp)
                    is_password_correct = salt_rehashed_pass == user.password
                    if is_password_correct:
                        return {'token': str(user.token), 'pin': ng.make_user_pin(user.email, user.token)}, 200
                    else:
                        return var.json_failure, 401
                else:
                    return var.json_failure, 404
            else:
                return var.json_failure, 404
        elif page == 'register':
            if phase == 0:
                # Receive posted variables
                received_email = request.json['email']

                # Check authorized && available (not already registered - AKA no inputs profile) emails
                authorized_emails = pd.read_csv(
                    var.PATH_AUTHORIZED_EMAILS, header=None)
                is_email_authorized = authorized_emails[0].str.fullmatch(
                    received_email).any()
                is_email_available = received_email not in os.listdir(
                    var.PATH_INPUTS)

                if is_email_authorized and is_email_available:
                    generated_token = ng.get_random_n(digits=6)
                    generated_salt_exp = ng.get_random_n(digits=2)
                    # Send the user a token to confirm they own the email

                    # email_sender.send_email(
                    #     received_email, generated_token, None)
                    print(generated_token)

                    # Make new user and commit to DB if none exists, else update it with new values
                    if UserModel.query.filter_by(email=received_email).first() is None:
                        user_new = UserModel(
                            received_email, generated_token, generated_salt_exp, None)
                        db.session.add(user_new)
                        print(f'Writing {user_new.email} to database...')
                        db.session.commit()
                    else:
                        user = UserModel.query.filter_by(
                            email=received_email).first()
                        user.token = generated_token
                        user.salt_exp = generated_salt_exp
                        print(f'Updating {user.email} values in database...')
                        db.session.commit()

                    return var.json_success, 200
                elif not is_email_authorized:
                    return var.json_failure, 401
                else:
                    return var.json_failure, 409
            elif phase == 1:
                # Receive posted variables
                received_email = request.json['email']
                received_token = str(request.json['token'])

                # Cross reference against recently generated and stored token
                user_token = UserModel.query.filter_by(
                    email=received_email).first().token

                if received_token == str(user_token):
                    return var.json_success, 200
                else:
                    return var.json_failure, 401
            elif phase == 2:
                # Receive posted variables
                received_email = request.json['email']
                received_token = str(request.json['token'])
                received_hashed_pass = request.json['hashedPass']

                # Pull relevant user data
                user = UserModel.query.filter_by(email=received_email).first()
                user_token = user.token
                user_salt_exp = user.salt_exp

                # Cross reference again
                if received_token == str(user_token):
                    # Generate salt re-hashed password
                    password = ng.rehash_password(
                        received_hashed_pass, user_token, user_salt_exp)

                    # Commit to DB
                    user.password = password
                    db.session.commit()

                    # Generate user profile in inputs, making further registration unavailable
                    os.mkdir(os.path.join(var.PATH_INPUTS, received_email))
                    print(f'Created {user.email} input profile...')
                else:
                    return var.json_failure, 401
            else:
                return var.json_failure, 404


class DashResource(Resource):
    def get(self, page, index):
        if page == 'process':
            user_email = request.headers['email']
            if index == 0:
                #Head & Neck
                # main_head_neck.main(user_email)
                email_sender.send_email(
                    user_email, None, os.path.join(var.name_dir_output, user_email, var.name_output_file))
                print(f'Email sent to: {user_email}')
                shutil.rmtree(os.path.join(var.name_dir_output, user_email))
                return var.json_success, 200
            else:
                return var.json_failure, 400
        elif page == 'image':
            user_email = request.headers['email']
            code = img.get_random_image_base64text(user_email)
            return {var.str_base64_key: code}, 200
        else:
            return var.json_failure, 400

    def post(self, page, index):
        if page == var.str_page_upload:
            user_email = request.form['email']
            user_token = request.form['token']
            user_pin = request.form['pin']
            is_authenticated = user_pin == ng.make_user_pin(user_email, user_token)
            if is_authenticated:
                path_upload = os.path.join(var.PATH_INPUTS, user_email)
                file_uploaded = request.files['fileDicom']
                file_uploaded.save(path_upload + f'/CT_{index}.dcm')
                return var.json_success, 200
            else:
                return var.json_failure, 403
        else:
            return var.json_failure, 400
