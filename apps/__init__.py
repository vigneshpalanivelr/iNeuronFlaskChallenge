"""
Initializing and Loading the Application
"""
import logging
import importlib
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_pymongo import PyMongo


mysqlDB = SQLAlchemy()
mongoDB = PyMongo()
logger = logging.getLogger(__name__)


def register_extentions(app):
    """
    Initializing the Databases
    """
    mongoDB.init_app(app)
    # mysqlDB.init_app(app)


def register_blueprints(app):
    """
    Registering the Flask Blueprint
    """
    for file_name in ['home', 'updatedata']:
        module = importlib.import_module(f'apps.{file_name}.routes')
        print(module.blueprint)
        app.register_blueprint(module.blueprint)


def configure_logger():
    """
    Configuring the Logging and file_handler
    """
    log_formatter = logging.Formatter('''[%(asctime)s] %(levelname)s in %(module)s: %(message)s''',
                                      datefmt="%Y-%m-%d %H:%M:%S")
    # add console handler to the root logger
    console_hanlder = logging.StreamHandler()
    console_hanlder.setFormatter(log_formatter)
    logger.addHandler(console_hanlder)

    # add file handler to the root logger
    file_handler = logging.FileHandler("apps/applog.log", mode='w')
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
    logger.setLevel('INFO')


def create_app(config):
    """
    Main Method
    """
    app = Flask(__name__)
    app.config.from_object(config)
    register_blueprints(app)
    register_extentions(app)
    configure_logger()
    return app
