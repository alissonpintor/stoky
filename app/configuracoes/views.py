from app import app, db, admin_permission
from flask import render_template, abort, make_response
from flask import request, redirect, url_for, flash
from flask_login import login_required, current_user

from . import configuracoes
from ..models import User, Role

from sqlalchemy.orm import exc
from sqlalchemy import exc as core_exc

# Formularios
from .forms import RegistrationForm, RolesForm

import datetime
import dateparser
from decimal import Decimal

TABLES = {'usuario': {'classe': User, 'url_padrao': 'configuracoes.usuarios'},
          'acesso': {'classe': Role, 'url_padrao': 'configuracoes.acessos'}}

# ROTA USADA PARA DELETAR OS REGISTROS
@configuracoes.route('/deletar/<path>/<id>')
@login_required
@admin_permission.require(http_exception=401)
def deletar(path, id):
    try:
        classe = TABLES[path]['classe']

        key = db.inspect(classe).primary_key[0].name

        query = classe.query.filter(classe.__dict__[key] == id).one()

        db.session.delete(query)
        db.session.commit()

        message = {'type': 'success', 'content': 'Registro excluido com sucesso'}
        flash(message)
        return redirect(url_for(TABLES[path]['url_padrao']))

    except exc.NoResultFound:
        message = {'type': 'error', 'content': 'Nao foi possivel excluir. Registro não existe'}
        flash(message)
        return redirect(url_for(TABLES[path]['url_padrao']))

    except core_exc.IntegrityError:
        message = {'type': 'error', 'content': 'Nao foi possivel excluir. Erro de Integridade'}
        flash(message)
        return redirect(url_for(TABLES[path]['url_padrao']))

@configuracoes.route('/usuarios', methods=['GET', 'POST'])
@configuracoes.route('/usuarios/<id>')
@login_required
@admin_permission.require(http_exception=401)
def usuarios(id=None):
    usuarios = User.query.order_by(User.username)
    classe = 'usuario'

    form = RegistrationForm()
    form.acesso.choices = [(r.id, r.name) for r in Role.query.all()]
    form.acesso.choices.insert(0, (0, ''))

    if form.validate_on_submit():
        usuario = User()
        if form.user_id.data != 0:
            usuario = User.query.filter_by(id=form.user_id.data).first()

        usuario.username = form.username.data
        usuario.password = form.password.data
        usuario.role_id = getattr(form.acesso, 'data', None)
        usuario.is_admin = form.is_admin.data

        try:
            db.session.add(usuario)
            db.session.commit()
            message = {'type': 'success', 'content': 'Registro cadastrado com sucesso'}
            flash(message)

        except Exception as e:
            message = {'type': 'success', 'content': 'Registro cadastrado com sucesso. Erro: {}'.format(e)}
            flash(message)

        redirect(url_for('configuracoes.usuarios'))

    if id:
        usuario = User.query.filter_by(id=id).first()
        form.user_id.data = usuario.id
        form.username.data = usuario.username
        form.acesso.data = usuario.role_id
        form.is_admin.data = usuario.is_admin

    return render_template('configuracoes/view_usuarios.html', title='Cadastro de Usuários', usuarios=usuarios, form=form, classe=classe)

@configuracoes.route('/acessos', methods=['GET', 'POST'])
@configuracoes.route('/acessos/<id>')
@login_required
@admin_permission.require(http_exception=401)
def acessos(id=None):
    acessos = Role.query.order_by(Role.name)
    classe = 'acesso'

    form = RolesForm()

    if form.validate_on_submit():
        acesso = Role()
        if form.role_id.data != 0:
            acesso = Role.query.filter_by(id=form.role_id.data).first()

        acesso.name = form.acesso.data
        acesso.description = form.descricao.data

        try:
            db.session.add(acesso)
            db.session.commit()
            message = {'type': 'success', 'content': 'Registro cadastrado com sucesso'}
            flash(message)

        except Exception as e:
            message = {'type': 'success', 'content': 'Registro cadastrado com sucesso. Erro: {}'.format(e)}
            flash(message)

        redirect(url_for('configuracoes.acessos'))

    if id:
        acesso = Role.query.filter_by(id=id).first()
        form.role_id.data = acesso.id
        form.acesso.data = acesso.name
        form.descricao.data = acesso.description

    return render_template('configuracoes/view_acessos.html', title='Cadastro de Acessos', acessos=acessos, form=form, classe=classe)
