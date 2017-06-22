from app import app, db, vendas_permission
from flask import render_template, abort, make_response
from flask import request, redirect, url_for, flash
from flask_weasyprint import HTML, render_pdf
from flask_login import login_required, current_user

from . import metas
from ..models import Vendedor, GruposDeVendedores, StokyMetasView, Marcas, MetaVendas, AssMetasVendedor, ClienteFornecedor

from sqlalchemy.orm import exc
from sqlalchemy import exc as core_exc

# Formularios
from .forms import VendedorForm, ResultadosForm, GrupoForm, MetaVendaForm, VendedorMetasForm

import datetime
import dateparser
from decimal import Decimal

TABLES = {'vendedor': {'classe': Vendedor, 'url_padrao': 'metas.vendedores'},
          'grupo': {'classe': GruposDeVendedores, 'url_padrao': 'metas.grupos'},
          'meta': {'classe': MetaVendas, 'url_padrao': 'metas.metas_vendas'}}

# FUNCOES AUXILIARES
def parseStrToFloat(value):
    value = value.replace('.','')
    value = value.replace(',','.')
    return value

def format_date(userdate):
    date = dateparser.parse(userdate, date_formats=['%Y-%m-%d'])
    try:
        return datetime.strftime(date)
    except TypeError:
        return None

# ROTA USADA PARA DELETAR OS REGISTROS
@metas.route('/deletar/<path>/<id>')
@login_required
@vendas_permission.require(http_exception=401)
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

@metas.route('/vendedores', methods=['POST', 'GET'])
@metas.route('/vendedores/<id>')
@login_required
@vendas_permission.require(http_exception=401)
def vendedores(id=None):
    vendedores = Vendedor.query.filter(Vendedor.flag_inativo == False)
    active_table = {}
    active_table['tab1'] = 'active'
    active_table['tab2'] = ''
    if request.args.get('flag_inativo'):
        active_table['tab1'] = ''
        active_table['tab2'] = 'active'
        if request.args.get('flag_inativo') == 'inativo':
            vendedores = Vendedor.query.filter(Vendedor.flag_inativo == True)
        if request.args.get('flag_inativo') == 'todos':
            vendedores = Vendedor.query.all()
    classe = 'vendedor'
    form = VendedorForm()

    if form.validate_on_submit():
        vendedor = Vendedor()
        if form.id_vendedor.data != 0:
            vendedor = Vendedor.query.filter(Vendedor.id_vendedor == form.id_vendedor.data).one()

        #query_ciss = ClienteFornecedor.query.filter_by(id_cli_for=form.id_vendedor_ciss.data).first()
        vendedor.id_vendedor_ciss = form.id_vendedor_ciss.data
        vendedor.nome_vendedor = form.nome_vendedor.data
        vendedor.flag_inativo = form.flag_inativo.data

        db.session.add(vendedor)
        db.session.commit()

        message = {'type': 'success', 'content': 'Registro cadastrado com sucesso.'}
        flash(message)

        return redirect(url_for('metas.vendedores'))

    # Verifica se foi passado o id pela url para buscar o registro para ser alterado
    if id:
        vendedor = Vendedor.query.filter(Vendedor.id_vendedor == id).one()
        form.id_vendedor.data = vendedor.id_vendedor
        form.id_vendedor_ciss.data = vendedor.id_vendedor_ciss
        form.nome_vendedor.data = vendedor.nome_vendedor
        form.flag_inativo.data = vendedor.flag_inativo

    return render_template('metas/view_vendedores.html', title='Cadastro de Vendedores', vendedores=vendedores, classe=classe, form=form, active_table=active_table)

@metas.route('/grupos', methods=['GET', 'POST'])
@metas.route('/grupos/<id>')
@login_required
@vendas_permission.require(http_exception=401)
def grupos(id=None):
    grupos = GruposDeVendedores.query.order_by(GruposDeVendedores.nome_grupo)
    classe = 'grupo'

    form = GrupoForm()
    vendedores = Vendedor.query.all()
    form.vendedores.choices = [(v.id_vendedor, '{0} - {1}'.format(v.id_vendedor_ciss, v.nome_vendedor)) for v in vendedores]

    if form.validate_on_submit():
        grupo = GruposDeVendedores()
        grupo.nome_grupo = form.nome_grupo.data

        lista_vendedores = [v for v in form.vendedores.data]
        if form.id_grupo.data != 0:
            grupo = GruposDeVendedores.query.filter(GruposDeVendedores.id_grupo == form.id_grupo.data).one()
            vendedores_form = [v for v in form.vendedores.data]
            vendedore_obj = [v.id_vendedor for v in grupo.vendedores]
            lista_vendedores = set(vendedores_form) - set(vendedore_obj)
            lista = set(vendedore_obj) - set(vendedores_form)
            for v in Vendedor.query.filter(Vendedor.id_vendedor.in_(lista)):
                grupo.vendedores.remove(v)

        for v in lista_vendedores:
            vendedor = Vendedor.query.filter(Vendedor.id_vendedor == v).one()
            grupo.vendedores.append(vendedor)

        db.session.add(grupo)
        db.session.commit()

        message = {'type': 'success', 'content': 'Registro cadastrado com sucesso'}
        flash(message)

        redirect(url_for('metas.grupos'))

    if id:
        grupo = GruposDeVendedores.query.filter(GruposDeVendedores.id_grupo == id).one()
        form.id_grupo.data = grupo.id_grupo
        form.nome_grupo.data = grupo.nome_grupo
        form.vendedores.data = [v.id_vendedor for v in grupo.vendedores]

    return render_template('metas/view_grupos.html', title='Cadastro de Grupos', grupos=grupos, form=form, classe=classe)

@metas.route('/metas_vendas', methods=['POST', 'GET'])
@metas.route('/metas_vendas/<id>')
@login_required
@vendas_permission.require(http_exception=401)
def metas_vendas(id=None):
    metas = MetaVendas.query.order_by(MetaVendas.dt_inicial)
    vendedores_metas = {}
    vendedores = Vendedor.query.filter(Vendedor.flag_inativo == False).order_by(Vendedor.nome_vendedor)

    for m in metas:
        vendedores_metas[m.id_meta] = []
        for v in m.vendedores:
            data = {}
            data['cod_ciss'] = v.vendedor.id_vendedor_ciss
            data['nome'] = v.vendedor.nome_vendedor
            data['meta_min'] = str(v.val_meta_min_vendedor)
            data['meta'] = str(v.val_meta_vendedor)
            vendedores_metas[m.id_meta].append(data)

    form = MetaVendaForm()
    if form.validate_on_submit():
        meta_venda = MetaVendas()
        ass_vendedor_meta = None

        if form.id_meta.data:
            try:
                meta_venda = MetaVendas.query.filter(MetaVendas.id_meta == form.id_meta.data).one()
                association = AssMetasVendedor.query.filter(AssMetasVendedor.id_meta_id == form.id_meta.data)
                for a in association:
                    meta_venda.vendedores.remove(a)
                    db.session.commit()
            except exc.NoResultFound:
                message = {'type': 'warning', 'content': 'O registro não foi encontrado'}
                flash(message)
                redirect(url_for('metas.metas_vendas'))

        meta_venda.nome_meta = form.nome_meta.data
        meta_venda.dt_inicial = dateparser.parse(form.data_inicial.data, date_formats=['%d-%m-%Y'])
        meta_venda.dt_final = dateparser.parse(form.data_final.data, date_formats=['%d-%m-%Y'])
        meta_venda.valor_meta = Decimal(form.valor_meta.data)
        meta_venda.valor_meta_minimo = None
        if form.valor_meta_minimo.data != '':
            meta_venda.valor_meta_minimo = Decimal(form.valor_meta_minimo.data)

        for vform in form.vendedores:
            if vform.flag_selecionar.data:
                a = AssMetasVendedor()
                a.val_meta_vendedor = Decimal(vform.valor_meta.data)
                a.val_meta_min_vendedor = None
                if vform.valor_meta_minimo.data != '':
                    a.val_meta_min_vendedor = Decimal(vform.valor_meta_minimo.data)
                v = Vendedor.query.filter(Vendedor.id_vendedor == vform.id_vendedor.data).one()
                meta_venda.vendedores.append(a)
                a.vendedor = v

        try:
            db.session.add(meta_venda)
            db.session.commit()
            message = {'type': 'success', 'content': 'Registro cadastrado com sucesso'}
            flash(message)
            return redirect(url_for('metas.metas_vendas'))

        except Exception as e:
            message = {'type': 'error', 'content': 'Erro ao cadastrar registo'}
            flash(message)
            return redirect(url_for('metas.metas_vendas'))

    if id:
        try:
            meta = MetaVendas.query.filter(MetaVendas.id_meta == id).one()
            form.id_meta.data = meta.id_meta
            form.nome_meta.data = meta.nome_meta
            form.data_inicial.data = meta.dt_inicial.strftime('%d-%m-%Y')
            form.data_final.data = meta.dt_final.strftime('%d-%m-%Y')
            form.valor_meta_minimo.data = meta.valor_meta_minimo
            form.valor_meta.data = meta.valor_meta

            id_vendedores = []
            for v in meta.vendedores:
                vendedor = VendedorMetasForm()
                vendedor.id_vendedor = v.vendedor.id_vendedor
                vendedor.nome_vendedor = v.vendedor.nome_vendedor
                vendedor.valor_meta_minimo = v.val_meta_min_vendedor
                vendedor.valor_meta = v.val_meta_vendedor
                id_vendedores.append(v.vendedor.id_vendedor)
                form.vendedores.append_entry(vendedor)

            for v in Vendedor.query.filter(~Vendedor.id_vendedor.in_(id_vendedores)):
                vendedor = VendedorMetasForm()
                vendedor.id_vendedor = v.id_vendedor
                vendedor.nome_vendedor = v.nome_vendedor
                vendedor.valor_meta_minimo = None
                vendedor.valor_meta = None
                vendedor.flag_selecionar = False
                form.vendedores.append_entry(vendedor)
        except exc.NoResultFound:
            message = {'type': 'warning', 'content': 'O registro não foi encontrado'}
            flash(message)
            redirect(url_for('metas.metas_vendas'))


    elif len(form.vendedores) == 0:
        for v in vendedores:
            vendedor = VendedorMetasForm()
            vendedor.id_vendedor = v.id_vendedor
            vendedor.nome_vendedor = v.nome_vendedor
            vendedor.valor_meta_minimo = None
            vendedor.valor_meta = None
            vendedor.flag_selecionar = False
            form.vendedores.append_entry(vendedor)

    classe = 'meta'

    return render_template('metas/view_metas.html', title='Cadastro de Metas', form=form,  metas=metas, vendedores_metas=vendedores_metas, classe=classe)

@metas.route('/resultados', methods=['GET', 'POST'])
@login_required
@vendas_permission.require(http_exception=401)
def resultados():

    vendedores=None
    meta=None
    total_vendas={'valor': 0, 'perc': 0}
    total_grupo={'valor': 0, 'perc': 0}
    outros=None

    form = ResultadosForm()
    form.metas.choices = [(m.id_meta, m.nome_meta) for m in MetaVendas.query.all()]
    #if request.method == 'POST':
    if form.validate_on_submit():
        meta = MetaVendas.query.filter_by(id_meta = form.metas.data).one()
        id_vendedores = [v.vendedor.id_vendedor_ciss for v in meta.vendedores]
        vendedores = []

        for v in meta.vendedores:
            # Define as colunas que vao ser retornadas na consulta em StokyMetasView
            query_ciss = db.session.query(db.func.sum(StokyMetasView.val_venda).label('val_bruto'),\
                                          db.func.sum(StokyMetasView.val_devolucao).label('val_dev'),\
                                          (db.func.sum(StokyMetasView.val_venda) + db.func.sum(StokyMetasView.val_devolucao)).label('val_liquido'))

            # Define os filtros da consulta
            query_ciss = query_ciss.filter(StokyMetasView.dt_movimento.between(meta.dt_inicial, meta.dt_final))\
                                   .filter(StokyMetasView.id_vendedor == v.vendedor.id_vendedor_ciss).first()

            if query_ciss:
                vendedor = {}
                vendedor['id_ciss'] = v.vendedor.id_vendedor_ciss
                vendedor['nome_vendedor'] = v.vendedor.nome_vendedor
                vendedor['val_bruto'] = query_ciss.val_bruto if query_ciss.val_bruto else 0
                vendedor['val_dev'] = query_ciss.val_dev if query_ciss.val_dev else 0
                vendedor['val_vendido'] = query_ciss.val_liquido if query_ciss.val_liquido else 0
                vendedor['val_meta_minimo'] = v.val_meta_min_vendedor
                vendedor['val_meta'] = v.val_meta_vendedor
                vendedor['perc_atingido'] = (query_ciss.val_liquido * 100)/v.val_meta_vendedor if query_ciss.val_liquido else 0
                total_grupo['valor'] += query_ciss.val_liquido if query_ciss.val_liquido else 0
                vendedores.append(vendedor)
        total_grupo['perc'] = (total_grupo['valor'] * 100)/meta.valor_meta

        # Define as colunas que vao ser retornadas na consulta em StokyMetasView
        outros = db.session.query(db.func.sum(StokyMetasView.val_venda).label('val_bruto'),\
                                  db.func.sum(StokyMetasView.val_devolucao).label('val_dev'),\
                                  (db.func.sum(StokyMetasView.val_venda) + db.func.sum(StokyMetasView.val_devolucao)).label('val_liquido'))

        # Define os filtros da consulta
        outros = outros.filter(StokyMetasView.dt_movimento.between(meta.dt_inicial, meta.dt_final))\
                               .filter(~StokyMetasView.id_vendedor.in_(id_vendedores)).one()

        # Define as colunas que vao ser retornadas na consulta em StokyMetasView
        query_total_vendas = db.session.query(db.func.sum(StokyMetasView.val_venda).label('val_bruto'),\
                                              db.func.sum(StokyMetasView.val_devolucao).label('val_dev'),\
                                              (db.func.sum(StokyMetasView.val_venda) + db.func.sum(StokyMetasView.val_devolucao)).label('valor'))
        # Define os filtros da consulta
        query_total_vendas = query_total_vendas.filter(StokyMetasView.dt_movimento.between(meta.dt_inicial, meta.dt_final)).one()
        total_vendas['val_bruto'] = query_total_vendas.val_bruto
        total_vendas['val_dev'] = query_total_vendas.val_dev
        total_vendas['valor'] = query_total_vendas.valor
        total_vendas['perc'] = (query_total_vendas.valor * 100)/meta.valor_meta

    return render_template('metas/view_resultados.html', title='Resultados', vendedores=vendedores, outros=outros, meta=meta, total_grupo=total_grupo, total_vendas=total_vendas, form=form)
