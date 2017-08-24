from flask import flash, redirect, render_template, url_for, request, current_app, session
from flask_login import login_required, login_user, logout_user, current_user
from flask_principal import Identity, AnonymousIdentity, identity_changed, identity_loaded, RoleNeed, UserNeed
from app import app

from . import auth
from .forms import LoginForm
from .. import db
from ..models import User, Role

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle requests to the /login route
    Log an employee in through the login form
    """
    form = LoginForm()
    if form.validate_on_submit():

        # check whether employee exists in the database and whether
        # the password entered matches the password in the database
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            # log employee in
            login_user(user)

            # Tell Flask-Principal the identity changed
            identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))

            # redirect to the dashboard page after login
            return redirect(request.args.get('next') or url_for('index'))

        # when login details are incorrect
        else:
            message = {'type': 'warning', 'content': 'Usuário ou senha inválido.'}
            flash(message)

    # load login template
    return render_template('auth/login.html', form=form, title='Login')

@auth.route('/logout')
@login_required
def logout():
    """
    Handle requests to the /logout route
    Log an employee out through the logout link
    """
    logout_user()

    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),  identity=AnonymousIdentity())

    message = {'type': 'sucess', 'content': 'Logged out efetuado com sucesso.'}
    flash(message)

    # redirect to the login page
    return redirect(url_for('auth.login'))

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    if hasattr(current_user, 'is_admin'):
        if current_user.is_admin:
            roles = Role.query.all()
            for role in roles:
                identity.provides.add(RoleNeed(role.name))
        elif hasattr(current_user, 'role'):
            role = current_user.role
            identity.provides.add(RoleNeed(role.name))
