from flask import Flask
from flask_restful import Api
from flask_cors import CORS

from models import db, init_db
from resources import TestResource, UserResource, DashResource
import global_vars as var

app = Flask(__name__)
cors = CORS(app)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{var.PATH_DATABASE}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    init_db()

api.add_resource(TestResource, '/test')
api.add_resource(UserResource, '/user/<string:page>/<int:phase>')
api.add_resource(DashResource, '/dash/<string:page>/<int:index>')

if __name__ == '__main__':
    app.run(debug=True)
