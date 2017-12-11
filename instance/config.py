# instance/config.py

SECRET_KEY              = 'p9Bv<3Eid9%$i01'
# SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
SQLALCHEMY_DATABASE_URI = 'postgresql://alisson:stoky@192.168.104.24:5432/stoky'
SQLALCHEMY_BINDS        = {'ciss': 'db2+ibm_db://dba:overhead@192.168.104.3:50000/STOKY',
                           'wms' : 'oracle://fullwms:fullwms@192.168.104.4'}

# Flask-Mail configuration
MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'alisson.stoky@gmail.com '
MAIL_PASSWORD = 'dota@pro'
MAIL_DEFAULT_SENDER = 'flask@example.com'
