from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_principal import Principal, Permission, RoleNeed

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_BINDS'] = {'ciss': 'db2+ibm_db://dba:overhead@192.168.104.3:50000/STOKY',
                                  'wms': 'oracle://fullwms:fullwms@192.168.104.4'}
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = 'some_secret'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = {'type': 'warning', 'content': "Você precisa estar logado para acessar esta página."}
login_manager.login_view = "auth.login"

db = SQLAlchemy(app)
from app import models
db.create_all(bind=None)

principals = Principal(app)
admin_permission = Permission(RoleNeed('admin'))
compras_permission = Permission(RoleNeed('admin'), RoleNeed('compras'))
vendas_permission = Permission(RoleNeed('admin'), RoleNeed('vendas'))
logistica_permission = Permission(RoleNeed('admin'), RoleNeed('logistica'))

exist_admin = db.session.query(db.exists().where(models.User.username == 'admin')).scalar()
if not exist_admin:
    admin = models.User(email="admin@admin.com",username="admin",password="admin2016",is_admin=True)
    db.session.add(admin)
    db.session.commit()

from .configuracoes import configuracoes as configuracoes_blueprint
#print(dir(configuracoes_blueprint.url_value_preprocessor))
app.register_blueprint(configuracoes_blueprint, url_prefix='/configuracoes')

from .tributacao import tributacao as tributacao_blueprint
app.register_blueprint(tributacao_blueprint, url_prefix='/tributacao')

from .metas import metas as metas_blueprint
app.register_blueprint(metas_blueprint, url_prefix='/metas')

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
