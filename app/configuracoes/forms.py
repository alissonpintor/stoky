from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField, BooleanField, IntegerField, ValidationError, SelectField
from wtforms.validators import DataRequired, EqualTo

from ..models import User, Role

class RegistrationForm(FlaskForm):
    """
    Form for users to create new account
    """
    user_id = IntegerField('Id', default=0)
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Password', validators=[
                                        DataRequired(),
                                        EqualTo('confirm_password', message='A senha deve ser idêntica a confirmação de senha')
                                        ])
    confirm_password = PasswordField('Confirm Password', default=False)
    acesso = SelectField('Acesso', choices=[], coerce=int)
    is_admin = BooleanField('Conta Admin')
    submit = SubmitField('Cadastrar')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('O nome do usuário já esta sendo usado.')

    def validate_acesso(form, field):
        if not form.is_admin.data:
            if field.data == 0:
                raise ValidationError('O tipo de acesso é obrigatório quando a conta não e Admin.')

class RolesForm(FlaskForm):
    """
    Form for create new roles
    """
    role_id = IntegerField('Id', default=0)
    acesso = StringField('Acesso', validators=[DataRequired()])
    descricao = StringField('Descrição')
    submit = SubmitField('Cadastrar')

    def validate_acesso(self, field):
        if Role.query.filter_by(name=field.data).first():
            raise ValidationError('O nome do acesso já esta existe.')
