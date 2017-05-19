from flask import Blueprint

metas = Blueprint('metas', __name__)

from . import views
