from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, IntegerField, BooleanField, SelectField, SelectMultipleField
#from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, InputRequired

class AutroizacaoForm(FlaskForm):
    numero = IntegerField('Nº aut.', validators=[DataRequired(message='Campo Obrigatório')])
    submit = SubmitField('Buscar')
