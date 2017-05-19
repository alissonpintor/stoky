from flask import Blueprint

configuracoes = Blueprint('configuracoes', __name__)

from . import views
