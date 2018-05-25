from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, IntegerField, BooleanField, SelectField
from wtforms import SelectMultipleField, DecimalField, DateField, HiddenField
from wtforms import DateField, DecimalField, FieldList, FormField
from wtforms.validators import ValidationError, DataRequired, InputRequired, Optional

from datetime import datetime
import dateparser

def format_date(userdate):
    date = dateparser.parse(userdate)
    try:
        return datetime.strftime(date, "%d-%m-%Y")
    except TypeError:
        return None

class TarefasForm(FlaskForm):
    id_tarefa = IntegerField('Cod.', default=0)
    nome_tarefa = StringField('Descrição', validators=[DataRequired(message='Campo Obrigatório')])
    lista_ids_wms = StringField('Lista de IDs', validators=[DataRequired(message='Campo Obrigatório')])
    valor_meta = DecimalField('Valor Meta.', places=2, validators=[DataRequired(message='Campo Obrigatório')])
    flag_meta_variavel = BooleanField('Meta variável')
    qtdade_min_colaborador = IntegerField('Qtdade Colaboradores', default=1)
    submit = SubmitField('Cadastrar')

class ParametrosForm(FlaskForm):
    id = IntegerField('Cod.', default=0)
    descricao = StringField('Descricão', validators=[DataRequired(message='Campo Obrigatório')])
    colaboradores_excluidos = SelectMultipleField('Lista de Colaboradores Fora da meta', coerce=int, validators=[DataRequired(message='Campo Obrigatório')])
    valor_meta_diario = DecimalField('Valor da Meta diario padrao', places=2, validators=[DataRequired(message='Campo Obrigatório')])
    submit = SubmitField('Cadastrar')

class BuscarMetasForm(FlaskForm):
    data_inicial = StringField('Data Inicial')
    data_final = StringField('Data Final')
    parametros = SelectField('Parametros', coerce=int, validators=[DataRequired(message='Campo Obrigatório')])
    submit = SubmitField('Buscar')

    def validate_data_final(form, field):
        dt_inicial = format_date(form.data_inicial.data)
        dt_final = format_date(field.data)
        if dt_final is None:
            raise ValidationError('Com o flag Buscar por data marcado a Data Final e obrigatorio')
        if dt_inicial and dt_final < dt_inicial:
            raise ValidationError('A data Final deve ser maior que a Inicial')

    def validate_data_inicial(form, field):
        dt_inicial = format_date(field.data)
        if dt_inicial is None:
            raise ValidationError('Com o flag Buscar por data marcado a Data Inicial e obrigatorio')

class BuscarPeriodoForm(FlaskForm):
    data_inicial = StringField('Data Inicial')
    data_final = StringField('Data Final')
    tempo = IntegerField('Tempo Max.', default=30)
    submit = SubmitField('Buscar')

    def validate_data_final(form, field):
        dt_inicial = format_date(form.data_inicial.data)
        dt_final = format_date(field.data)
        if dt_final is None:
            raise ValidationError('Com o flag Buscar por data marcado a Data Final e obrigatorio')
        if dt_inicial and dt_final < dt_inicial:
            raise ValidationError('A data Final deve ser maior que a Inicial')

    def validate_data_inicial(form, field):
        dt_inicial = format_date(field.data)
        if dt_inicial is None:
            raise ValidationError('Com o flag Buscar por data marcado a Data Inicial e obrigatorio')

class ErrosForm(FlaskForm):
    id_erro = IntegerField('Cod.', default=0)
    nome_erro = StringField('Descrição', validators=[DataRequired(message='Campo Obrigatório')])
    tarefa = SelectField('Tarefa', choices=[], coerce=int, validators=[DataRequired(message='Campo Obrigatório')])
    submit = SubmitField('Cadastrar')


# Formularios dos Relatorios
class FormRomaneioSeparacao(FlaskForm):
    onda_id = IntegerField('Onda')
    submit = SubmitField('Gerar')
