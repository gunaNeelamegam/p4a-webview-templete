from flask import Flask

## creating the flask app
flask_app = Flask(__name__, template_folder="../templates", static_folder="../static")

from routes import FlaskApp