from app import app, db, compras_permission
from flask import render_template, abort, make_response, session
from flask import request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..models import Ncm, Produto, ProdutoGrade, ConfereMercadoria, ProdutoTributacao

from . import tributacao

# Formularios
from .forms import AutroizacaoForm

# @admin_permission.require(http_exception=401)
@tributacao.route('/ajusta_tributacao', methods=['GET', 'POST'])
@login_required
@compras_permission.require(http_exception=401)
def ajusta_tributacao():
    produtos = None
    nota = None

    form = AutroizacaoForm()
    if request.form.get('table_form'):
        if 'id_autorizacao' in session:
            autorizacao = ConfereMercadoria.query.filter(ConfereMercadoria.id_autorizacao == session['id_autorizacao'])

            if autorizacao.first():
                uf_fornecedor = autorizacao[0].autorizacao.fornecedor.uf_cli_for
                prod_principal = [p.id_produto for p in autorizacao]
                prods = [p.id_subproduto for p in autorizacao]

                for id_prod in prod_principal:
                    p = Produto.query.filter(Produto.id_produto == id_prod).one()
                    p.per_ipi = 0
                    p.per_ipi_saida = 0
                    p.id_cst_ipi_entrada = 49
                    p.id_cst_ipi_saida = 99
                    p.id_eqp_entrada = None
                    p.id_eqp_saida = None

                    db.session.add(p)
                    db.session.commit()

                produto_tributacao_mt = ProdutoTributacao.query.filter(ProdutoTributacao.id_subproduto.in_(prods))\
                                                            .filter(ProdutoTributacao.uf == 'MT')
                for pt in produto_tributacao_mt:
                    radio_subst = request.form.get('{0}-substituido'.format(pt.id_subproduto))
                    radio_cgmedia = request.form.get('{0}-incentivo'.format(pt.id_subproduto))

                    produto_principal = pt.produto_grade_tributacao.produto
                    produto_principal.flag_trib_grupo = 'F'

                    pt.per_icms_ent = 17
                    pt.per_margem_subst = 45 if radio_cgmedia == 'F' else 0
                    pt.per_icms_subst = 7 if radio_cgmedia == 'F' else 17
                    pt.per_margem_original = 0
                    pt.tipo_trib_ent = 'F'
                    pt.id_sit_trib = 60

                    db.session.add(produto_principal)
                    db.session.add(pt)
                    db.session.commit()

                produto_tributacao_for = ProdutoTributacao.query.filter(ProdutoTributacao.id_subproduto.in_(prods))\
                                                            .filter(ProdutoTributacao.uf == uf_fornecedor)
                if uf_fornecedor != 'MT':
                    for pt in produto_tributacao_for:
                        radio_subst = request.form.get('{0}-substituido'.format(pt.id_subproduto))
                        radio_cgmedia = request.form.get('{0}-incentivo'.format(pt.id_subproduto))

                        produto_principal = pt.produto_grade_tributacao.produto
                        produto_principal.flag_trib_grupo = 'F'

                        pt.per_icms_ent = 0
                        pt.per_margem_subst = 45 if radio_cgmedia == 'F' else 0
                        pt.per_icms_subst = 7 if radio_cgmedia == 'F' else 0
                        pt.per_margem_original = 45
                        pt.tipo_trib_ent = 'F' if radio_subst == 'T' else 'T'
                        pt.id_sit_trib = 60 if radio_subst == 'T' else 90

                        db.session.add(produto_principal)
                        db.session.add(pt)
                        db.session.commit()

                message = {'type': 'success', 'content': 'Alterações realizadas com sucesso'}
                flash(message)
            else:
                message = {'type': 'warning', 'content': 'A autorização deve ser concluída no WMS primeiro.'}
                flash(message)
    else:
        if form.validate_on_submit():
            session['id_autorizacao'] = form.numero.data
            autorizacao = ConfereMercadoria.query.filter(ConfereMercadoria.id_autorizacao == form.numero.data)
            if autorizacao.first():
                produtos = autorizacao
                nota = autorizacao[0].autorizacao
            else:
                message = {'type': 'warning', 'content': 'A autorização não existe ou deve ser concluída no WMS primeiro.'}
                flash(message)

    return render_template('tributacao/view_ajusta_tributacao.html', title='Ajuste de tributação dos produtos', form=form, nota=nota, produtos=produtos)
