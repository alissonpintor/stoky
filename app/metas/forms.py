from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, IntegerField, BooleanField, SelectField, SelectMultipleField
from wtforms import DateField, DecimalField, FieldList, FormField, Field
from wtforms.fields.html5 import EmailField
from wtforms.validators import ValidationError, DataRequired, InputRequired, Regexp, Optional

from decimal import Decimal
from datetime import datetime
import dateparser

def format_date(userdate):
    date = dateparser.parse(userdate)
    try:
        return datetime.strftime(date, "%d-%m-%Y")
    except TypeError:
        return None

def is_decimal(form, field):
    try:
        float(field.data)
    except ValueError:
        raise ValidationError('informe somente numeros')

class VendedorForm(FlaskForm):
    id_vendedor = IntegerField('id_vendedor', validators=[], default=0)
    id_vendedor_ciss = IntegerField('id_vendedor_ciss', validators=[InputRequired(message='Campo Obrigatório')])
    nome_vendedor = StringField('nome_vendedor', validators=[DataRequired(message='Campo Obrigatório')])
    flag_inativo = BooleanField('Inativar')
    submit = SubmitField('Cadastrar', false_values=('false', 'f'), default='f')

class GrupoForm(FlaskForm):
    id_grupo = IntegerField('id_grupo', validators=None, default=0)
    nome_grupo = StringField('nome_grupo', validators=[DataRequired(message='Campo Obrigatório')])
    vendedores = SelectMultipleField('vendedores',
                                      choices=[],
                                      coerce=int,
                                      default='',
                                      validators=[InputRequired()])
    submit = SubmitField('Cadastrar')

class VendedorMetasForm(FlaskForm):
    id_vendedor = IntegerField('id', validators=[], default=0)
    nome_vendedor = StringField('Nome', validators=[DataRequired(message='Campo Obrigatório')])
    valor_meta_minimo = StringField('Valor Mínimo', validators=[Optional()])
    valor_meta = StringField('Valor')
    flag_selecionar = BooleanField('Selecionar')

    def validate_valor_meta(form, field):
        v_min = form.valor_meta_minimo.data
        if form.flag_selecionar.data:
            is_decimal(form, field)
            if Decimal(field.data) < 1:
                raise ValidationError('O valor da meta deve ser maior que 0.')
            if v_min != '' and Decimal(v_min) > 0:
                if Decimal(v_min) > Decimal(field.data):
                    raise ValidationError('O valor da meta deve ser maior que a meta minima.')

    def validate_valor_meta_minimo(form, field):
        if form.flag_selecionar.data:
            is_decimal(form, field)
            if field.data != '' and Decimal(field.data) < 1:
                raise ValidationError('O valor da meta mínima deve ser maior que 0.')

    class Meta:
        # This overrides the value from the base form.
        csrf = False

class MetaVendaForm(FlaskForm):
    id_meta = IntegerField('Id', validators=None, default=0)
    nome_meta = StringField('Descrição', validators=[DataRequired(message='Campo Obrigatório')])
    data_inicial = StringField('Data Inicial', validators=[InputRequired(message='Campo Obrigatório')])
    data_final = StringField('Data Final', validators=[InputRequired(message='Campo Obrigatório')])
    valor_meta_minimo = StringField('Valor Mínimo', validators=[Optional(), is_decimal])
    valor_meta = StringField('Valor', validators=[is_decimal, DataRequired(message='Campo Obrigatório')])
    flag_inativo = BooleanField('inativo')

    vendedores = FieldList(FormField(VendedorMetasForm), min_entries=0)
    submit = SubmitField('Cadastrar')

    def validate_valor_meta(form, field):
        v_min = form.valor_meta_minimo.data
        soma = 0

        for v in form.vendedores:
            if v.valor_meta.data != '':
                soma += Decimal(v.valor_meta.data)
        if field.data != '' and Decimal(field.data) < soma:
            raise ValidationError('O valor da meta deve ser maior que a soma da meta dos vendedores.')

        if Decimal(field.data) < 1:
            raise ValidationError('O valor da meta deve ser maior que 0.')

        if v_min != '' and Decimal(v_min) > 0:
            if Decimal(v_min) > Decimal(field.data):
                raise ValidationError('O valor da meta deve ser maior que a meta minima.')

    def validate_valor_meta_minimo(form, field):
        soma = 0
        for v in form.vendedores:
            if v.valor_meta_minimo.data != '':
                soma += Decimal(v.valor_meta_minimo.data)
        if field.data != '' and Decimal(field.data) < soma:
            raise ValidationError('O valor da meta mínima deve ser maior que a soma da meta minima dos vendedores.')

        if field.data != '' and Decimal(field.data) < 1:
            raise ValidationError('O valor da meta mínima deve ser maior que 0.')

    def validate_data_final(form, field):
        dt_inicial = format_date(form.data_inicial.data)
        dt_final = format_date(field.data)
        print(dt_inicial)
        print(dt_final)
        if dt_final is None:
            raise ValidationError('Com o flag Buscar por data marcado a Data Final e obrigatorio')
        if dt_inicial and dt_final < dt_inicial:
            raise ValidationError('A data Final deve ser maior que a Inicial')

    def validate_data_inicial(form, field):
        dt_inicial = format_date(field.data)
        if dt_inicial is None:
            raise ValidationError('Com o flag Buscar por data marcado a Data Inicial e obrigatorio')

class ResultadosForm(FlaskForm):
    metas = SelectField('Metas',
                        choices=[],
                        coerce=int,
                        default='',
                        validators=[InputRequired()])
    submit = SubmitField('Buscar')
