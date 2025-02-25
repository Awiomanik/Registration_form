from flask import Flask
from config.settings import load_config
import os

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Load default config
    app.config.from_object('config.settings.DefaultConfig')

    # Load sensitive config (SECRET_KEY) from instance/config.py
    app.config.from_pyfile('config.py', silent=True)

    # Initialize Routes
    from app.routes.main_routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app