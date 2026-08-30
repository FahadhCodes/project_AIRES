import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.config['SECRET_KEY'] = 'c9c98e71de7ede255622d858'
# BASE_DIR evaluates to: ...\AIRE_project\AIRE
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Point to: ...\AIRE_project\instance\aire.db
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'instance', 'aire.db'))

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
db = SQLAlchemy(app)
from AIRE import routes  # noqa
