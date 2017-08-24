from flask import Blueprint

tributacao = Blueprint('tributacao', __name__)

from . import views
