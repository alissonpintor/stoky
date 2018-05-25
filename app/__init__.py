from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_principal import Principal, Permission, RoleNeed
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import exc
from sqlalchemy import event
from sqlalchemy.pool import Pool

from config import app_config

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(app_config['dev'])
app.config.from_pyfile('config.py')

mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = {'type': 'warning', 'content': "Você precisa estar logado para acessar esta página."}
login_manager.login_view = "auth.login"

db = SQLAlchemy(app)
migrate = Migrate(app, db)
from app import models
db.create_all(bind=None)


@event.listens_for(db.engine, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        # optional - dispose the whole pool
        # instead of invalidating one at a time
        # connection_proxy._pool.dispose()

        # raise DisconnectionError - pool will try
        # connecting again up to three times before raising.
        raise exc.DisconnectionError()
    cursor.close()


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.close_all()


principals = Principal(app)
admin_permission = Permission(RoleNeed('admin'))
compras_permission = Permission(RoleNeed('admin'), RoleNeed('compras'))
vendas_permission = Permission(RoleNeed('admin'), RoleNeed('vendas'))
logistica_permission = Permission(RoleNeed('admin'), RoleNeed('logistica'))

exist_admin = db.session.query(db.exists().where(models.User.username == 'admin')).scalar()
exist_admin_role = db.session.query(db.exists().where(models.Role.name == 'admin')).scalar()
if not exist_admin:
    admin = models.User(email="admin@admin.com",username="admin",password="admin2016",is_admin=True)
    db.session.add(admin)
    db.session.commit()

if not exist_admin_role:
    admin_role = models.Role(name="admin", description="Acesso admin")
    db.session.add(admin_role)
    db.session.commit()

from .configuracoes import configuracoes as configuracoes_blueprint
#print(dir(configuracoes_blueprint.url_value_preprocessor))
app.register_blueprint(configuracoes_blueprint, url_prefix='/configuracoes')

from .tributacao import tributacao as tributacao_blueprint
app.register_blueprint(tributacao_blueprint, url_prefix='/tributacao')

from .vendas import vendas as vendas_blueprint
app.register_blueprint(vendas_blueprint, url_prefix='/vendas')

from .auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint, url_prefix='/auth')

from .wmserros import wmserros as wmserros_blueprint
app.register_blueprint(wmserros_blueprint, url_prefix='/wmserros')

Bootstrap(app)

# Root route
@app.route('/')
def index():
    return render_template('base.html')


# TEMPLATES PARA ERROS DE REQUISIÇÃO
@app.errorhandler(404)
def page_not_found(error):
    return render_template('errors_templates/page_not_found.html'), 404

@app.errorhandler(401)
def page_not_found(error):
    return render_template('errors_templates/unauthorized_access.html'), 401

@app.errorhandler(500)
def page_not_found(error):
    return render_template('errors_templates/unauthorized_access.html', error=error), 500
