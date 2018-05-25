from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, IntegerField, BooleanField
from wtforms import SelectField, SelectMultipleField, FormField, FieldList
from wtforms import DateField
from wtforms.validators import ValidationError
from app.utils.forms.wid import SelectWidget
#from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, InputRequired

from dateparser import parse

class AutroizacaoForm(FlaskForm):
    numero = IntegerField('Nº aut.', validators=[DataRequired(message='Campo Obrigatório')])
    submit = SubmitField('Buscar')


class FormInformarDescricao(FlaskForm):
    descricao = StringField(
        'Descrição',
        validators=[
            DataRequired(message='Campo Obrigatório')
        ]
    )
    dt_inicial = DateField(
        'Data Inicial',
        format='%d/%m/%Y',
        validators=[
            DataRequired(message='Campo Obrigatório')
        ]
    )
    dt_final = DateField(
        'Data Final',
        format='%d/%m/%Y',
        validators=[
            DataRequired(message='Campo Obrigatório')
        ]
    )
    submit = SubmitField('Próximo')

    @classmethod
    def validate_dt_final(cls, form, field):
        dt_inicial = form.dt_inicial.data
        dt_final = field.data
        if dt_final is None:
            raise ValidationError('Com o flag Buscar por data marcado a Data Final e obrigatorio')
        if dt_inicial and dt_final < dt_inicial:
            raise ValidationError('A data Final deve ser maior que a Inicial')

    @classmethod
    def validate_dt_inicial(cls, form, field):
        dt_inicial = field.data
        if dt_inicial is None:
            raise ValidationError('Com o flag Buscar por data marcado a Data Inicial e obrigatorio')


class ListagemLogisticaCidades(FlaskForm):
    cidades = SelectMultipleField(
        'Selecione as cidades', 
        coerce=str, 
        validators=[
            DataRequired(message='Campo Obrigatório')
        ])
    
    submit = SubmitField('Cadastrar')


class LogisticaPedidosForm(FlaskForm):
    pedidos = SelectMultipleField('Pedidos', choices=[])
    
    @classmethod
    def add_pedidos(cls, cidade, choices, default=None):
        field_description = 'Pedidos {}'.format(cidade.title())
        field = SelectMultipleField(field_description, coerce=int, choices=choices, default=default) 
        setattr(cls, 'pedidos', field)
        return cls

    class Meta:
        # This overrides the value from the base form.
        csrf = False


class ListagemLogisticaPedidos(FlaskForm):
    pedidos = SelectMultipleField(
        'Pedidos',
        coerce=int,
        validators=[
            DataRequired(message='Campo Obrigatório')
        ]
    )
    submit = SubmitField('Cadastrar')
