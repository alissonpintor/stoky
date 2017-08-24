from flask import Blueprint

wmserros = Blueprint('wmserros', __name__)

from . import views
