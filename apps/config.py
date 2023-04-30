"""
Loading the Configuration
"""
import sys
import os
from dotenv import load_dotenv


class Config():
    """
    Loading .env file to Environment Variable
    """
    load_dotenv()


class ProductionConfig(Config):
    """
    Configuration reading from .env file
    """
    # pylint: disable=consider-using-f-string
    DEBUG = False
    try:
        os.environ.get('AWS_S3_REGION_NAME')
        os.environ.get('AWS_S3_BUCKET_NAME')
        os.environ.get('AWS_ACCESS_KEY_ID')
        os.environ.get('AWS_SECRET_ACCESS_KEY')
        os.environ.get('MONGO_DB_COURSES')
        os.environ.get('MONGO_DB_COURSE_CATEGORY')
        os.environ.get('MONGO_DB_COURSE_BUNDLE_CATEGORY_COUNT')
        os.environ.get('MONGO_DB_COURSE_BUNDLE_COUNT')
        os.environ.get('APP_UPDATE_PASSWORD')

        SQLALCHEMY_DATABASE_URI = '{}+pymysql://{}:{}@{}:{}/{}'.format(
            os.environ.get('SQL_DB_ENGINE'),
            os.environ.get('SQL_DB_USERNAME'),
            os.environ.get('SQL_DB_PASSWORD'),
            os.environ.get('SQL_DB_HOSTNAME'),
            os.environ.get('SQL_DB_PORT'),
            os.environ.get('SQL_DB_NAME')
        )

        MONGO_URI = 'mongodb+srv://{}:{}@{}/{}?retryWrites=true&w=majority'.format(
            os.environ.get('MONGO_DB_USERNAME'),
            os.environ.get('MONGO_DB_PASSWORD'),
            os.environ.get('MONGO_DB_HOSTNAME'),
            os.environ.get('MONGO_DB_NAME')
        )
    except KeyError as e:
        sys.exit(f'Please provide DB credentials: {e}')


config_dict = {'Production': ProductionConfig}
