from flask import Blueprint

vendas = Blueprint('vendas', __name__)

from . import views
