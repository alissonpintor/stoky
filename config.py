# config.py

class Config(object):
    """
    Common configurations
    """

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPLATES_AUTO_RELOAD          = True
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    RESULT_BACKEND = 'redis://localhost:6379/0'

    # Put any configurations here that are common across all environments

class DevelopmentConfig(Config):
    """
    Development configurations
    """

    DEBUG           = True
    SQLALCHEMY_ECHO = False

class ProductionConfig(Config):
    """
    Production configurations
    """

    DEBUG = False
    SQLALCHEMY_POOL_RECYCLE = 3600
    SQLALCHEMY_POOL_TIMEOUT = 30

app_config = {
    'dev': DevelopmentConfig,
    'prod' : ProductionConfig
}
