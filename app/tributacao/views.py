from app import app, db, compras_permission
from flask import render_template, abort, make_response, session
from flask import request, redirect, url_for, flash
from flask_login import login_required, current_user
from wtforms import SelectMultipleField
from dateutil.parser import parse
from flask_weasyprint import HTML, render_pdf

from ..models import Ncm, Produto, ProdutoGrade, ConfereMercadoria, ProdutoTributacao
from app.models import WmsPedidos, WmsItensCheckout, WmsItems

from . import tributacao

# Formularios
from .forms import AutroizacaoForm, ListagemLogisticaCidades
from .forms import ListagemLogisticaPedidos, LogisticaPedidosForm
from .forms import FormInformarDescricao

# Import dos Utils
from app.utils.messages import success, info, warning, error


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


@tributacao.route('/relatorio/logistica/carga/periodo', methods=['GET', 'POST'])
@login_required
@compras_permission.require(http_exception=401)
def logistica_carga_descricao():
    """
        View para informar o nome e o periodo da carga
    """
    template = 'tributacao/view_carga_descricao.html'
    form = FormInformarDescricao()

    if form.validate_on_submit():
        session['descricao'] = form.descricao.data
        session['dt_inicial'] = form.dt_inicial.data
        session['dt_final'] = form.dt_final.data

        return redirect(url_for('tributacao.logistica_carga_cidades'))

    result = {
        'title': 'Montagem de Carga: Nome e Periodo',
        'form': form
    }

    return render_template(template, **result)


@tributacao.route('/relatorio/logistica/carga/cidades', methods=['GET', 'POST'])
@login_required
@compras_permission.require(http_exception=401)
def logistica_carga_cidades():
    """
        Utilizado para gerar a listagem de carregamento
        com os clientes por cidade e volumes
    """
    import datetime
    template = 'tributacao/view_listagem_cidades.html'
    form = ListagemLogisticaCidades()

    is_set = True 
    for v in ['dt_inicial', 'dt_final']:
        is_set = v in session    
    if not is_set:
        warning('O período e a descrição são obrigatórios.')
        return redirect(url_for('tributacao.logistica_carga_descricao'))

    if 'count' in session:
        session['count'] = 0
    
    if 'pedidos' in session:
        session['pedidos'] = []
    
    dt_inicial = parse(session['dt_inicial'])
    dt_final = parse(session['dt_final'])
    cidades = buscar_cidades_carga(dt_inicial, dt_final)

    form.cidades.choices = [(c.cidade, c.cidade) for c in cidades]
    cidades = [c.cidade for c in cidades]

    if form.validate_on_submit():
        choices = form.cidades.data
        session['cidades'] = choices

        cidades = list(filter(lambda x: x not in choices, cidades))        
        cidades = choices + cidades
        
        form.cidades.choices = [(c, c) for c in cidades]

        return redirect(url_for('tributacao.logistica_carga_pedidos'))

    result = {
        'title': 'Montagem de Carga: Seleção de Cidades',
        'form': form
    }

    return render_template(template, **result)


@tributacao.route('/relatorio/logistica/carga/cidade/{id}', methods=['GET'])
@tributacao.route('/relatorio/logistica/carga/cidade', methods=['GET', 'POST'])
@login_required
@compras_permission.require(http_exception=401)
def logistica_carga_pedidos(id=None):
    """
        Utilizado para gerar a listagem de carregamento
        com os clientes por cidade e volumes
    """
    template = 'tributacao/view_listagem_pedidos.html'
    form = ListagemLogisticaPedidos()

    # Verifica se o periodo e as cidades foram selecionados
    is_set = True 
    for v in ['cidades', 'dt_inicial', 'dt_final']:
        is_set = v in session    
    if not is_set:
        warning('O período e cidades são obrigatórios.')
        return redirect(url_for('tributacao.logistica_carga_cidades'))

    cidades = session['cidades']
    dt_inicial = parse(session['dt_inicial'])
    dt_final = parse(session['dt_final'])
    count = int(session['count']) if 'count' in session else 0
    cidade = cidades[count]
    total = int(len(cidades))

    pedidos = buscar_pedidos_carga(dt_inicial, dt_final, cidade)

    form.pedidos.label.text = 'Pedidos {}'.format(cidade.title())
    form.pedidos.choices = pedidos

    if form.validate_on_submit():
        if 'pedidos' not in session:
            session['pedidos'] = []
        
        session['pedidos'].extend(form.pedidos.data)
                
        count += 1
        
        if count < total:
            session['count'] = count
        else:
            return redirect(url_for('tributacao.logistica_carga_romaneio'))
    
        return redirect(url_for('tributacao.logistica_carga_pedidos'))

    result = {
        'title': 'Montagem de Carga: Seleção de Pedidos',
        'form': form
    }

    return render_template(template, **result)


@tributacao.route('/relatorio/logistica/romaneio-carga', methods=['GET', 'POST'])
@login_required
@compras_permission.require(http_exception=401)
def logistica_carga_romaneio():
    """
        Exibi o resultado final da carga montada
    """
    template = 'tributacao/view_listagem_romaneio.html'
    import datetime

    is_set = 'pedidos' in session
    if not is_set:
        warning('Nenhum pedido selecionado ainda.')
        return redirect(url_for('tributacao.logistica_carga_cidades'))
    
    dt_inicial = parse(session['dt_inicial'])
    dt_final = parse(session['dt_final'])
    dt_inicial = dt_inicial.strftime('%d/%m/%Y')
    dt_final = dt_final.strftime('%d/%m/%Y')
    
    pedidos = session['pedidos']
    pedidos = buscar_volumes_carga(pedidos)
    descricao = session['descricao']

    datahora = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    periodo_busca = '{} à {}'.format(dt_inicial, dt_final)

    result = {
        'title': 'Romaneio de Carregamento',
        'pedidos': pedidos,
        'datahora': datahora,
        'periodo_busca': periodo_busca,
        'descricao': descricao
    }

    return render_template(template, **result)


@tributacao.route('/relatorio/logistica/romaneio-carga-pdf', methods=['GET'])
@login_required
@compras_permission.require(http_exception=401)
def logistica_carga_romaneio_pdf():
    """
        Imprimi o resultado final da carga montada
    """
    template = 'tributacao/reports/report-carga.html'
    import datetime

    is_set = 'pedidos' in session
    if not is_set:
        warning('Nenhum pedido selecionado ainda.')
        return redirect(url_for('tributacao.logistica_carga_cidades'))
    
    dt_inicial = parse(session['dt_inicial'])
    dt_final = parse(session['dt_final'])
    dt_inicial = dt_inicial.strftime('%d/%m/%Y')
    dt_final = dt_final.strftime('%d/%m/%Y')
    
    pedidos = session['pedidos']
    pedidos = buscar_volumes_carga(pedidos)
    descricao = session['descricao']

    datahora = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    periodo_busca = '{} à {}'.format(dt_inicial, dt_final)

    result = {
        'title': 'Romaneio de Carregamento',
        'pedidos': pedidos,
        'datahora': datahora,
        'periodo_busca': periodo_busca,
        'descricao': descricao
    }

    html =  render_template(template, **result)
    return render_pdf(HTML(string=html))


def buscar_cidades_carga(dt_inicial, dt_final):
    """
        recebe a data inicial e final e busca
        as cidades que possuem pedidos separados
        no periodo informado
    """
    cidades = db.session.query(WmsPedidos.cidade)
    cidades = cidades.filter(
        WmsPedidos.situacao_erp == 6,
        WmsPedidos.dt_emissao >= dt_inicial,
        WmsPedidos.dt_emissao <= dt_final
    ).order_by(
        WmsPedidos.cidade
    ).distinct().all()

    return cidades


def buscar_cidade_pedido(dt_inicial, dt_final, id_pedido):
    """
        recebe a data inicial e final e busca
        as cidades que possuem pedidos separados
        no periodo informado
    """
    cidades = db.session.query(WmsPedidos.cidade)
    cidades = cidades.filter(
        WmsPedidos.situacao_erp == 6,
        WmsPedidos.dt_emissao >= dt_inicial,
        WmsPedidos.dt_emissao >= dt_final,
        WmsPedidos.id == id_pedido
    ).first()

    return cidades


def buscar_pedidos_carga(dt_inicial, dt_final, cidade):
    """
        recebe a data inicial e final e a cidade
        e retorna os pedidos do periodo feitos
        na cidade informada 
    """
    pedidos = db.session.query(
        WmsPedidos.id,
        WmsPedidos.num_pedido,
        WmsPedidos.nome_cliente,
        WmsPedidos.dt_emissao
    ).filter(
        WmsPedidos.situacao_erp == 6,
        WmsPedidos.dt_emissao >= dt_inicial,
        WmsPedidos.dt_emissao <= dt_final,
        WmsPedidos.cidade==cidade
    ).order_by(
        WmsPedidos.nome_cliente
    ).all()

    label = '{} - {} - {}'
    re = [
        (int(p.id), label.format(
            p.num_pedido,
            p.nome_cliente[:30].title(),
            p.dt_emissao
        )) for p in pedidos
    ]

    return re


def buscar_produtos_pedidos_carga(pedidos):
    """
        recebe a data inicial e final e a cidade
        e retorna os pedidos do periodo feitos
        na cidade informada 
    """
    from collections import OrderedDict as odict
    
    query = db.session.query(
        WmsPedidos.cidade,
        WmsPedidos.num_pedido,
        WmsPedidos.nome_cliente,
        WmsItensCheckout.num_volume,
        WmsItensCheckout.qtd_volume,
        WmsItems.idCiss,
        WmsItems.descricao
    ).join(
        WmsItensCheckout,
        WmsItems
    ).filter(
        WmsPedidos.situacao_erp == 6,
        WmsPedidos.id.in_(pedidos)
    ).all()

    cidades = odict()

    for p in query:
        clientes = cidades.setdefault(p.cidade, odict())
        pedidos = clientes.setdefault(p.nome_cliente, odict())
        volumes = pedidos.setdefault(p.num_pedido, odict())
        produtos = volumes.setdefault(p.num_volume, [])

        produtos.append({
            'cod': str(p.idCiss),
            'descricao': str(p.descricao),
            'qtdade': str(p.qtd_volume)
        })
    
    return cidades


def buscar_volumes_carga(pedidos):
    """
        recebe a data inicial e final e a cidade
        e retorna os pedidos do periodo feitos
        na cidade informada 
    """
    from collections import OrderedDict as odict
    
    query = db.session.query(
        WmsPedidos.cidade,
        WmsPedidos.num_pedido,
        WmsPedidos.dt_emissao,
        WmsPedidos.nome_cliente,
        WmsItensCheckout.num_volume
    ).join(
        WmsItensCheckout
    ).filter(
        WmsPedidos.situacao_erp == 6,
        WmsPedidos.id.in_(pedidos)
    ).distinct().subquery()

    querys = db.session.query(
        query.c.cidade,
        query.c.num_pedido,
        query.c.dt_emissao,
        query.c.nome_cliente,
        db.func.count(
            query.c.num_volume
        ).label('qtd_volumes')
    ).group_by(
        query.c.cidade,
        query.c.num_pedido,
        query.c.dt_emissao,
        query.c.nome_cliente
    ).all()

    cidades = odict()
    total_volumes = odict()
    for p in querys:
        clientes = cidades.setdefault(p.cidade, odict())
        pedidos = clientes.setdefault(p.nome_cliente, [])

        total = total_volumes.setdefault(p.nome_cliente, 0)
        total += p.qtd_volumes
        total_volumes[p.nome_cliente] = total
        
        pedidos.append({
            'numero': p.num_pedido,
            'emissao': p.dt_emissao,
            'volumes': p.qtd_volumes,
            'total': total
        })
    
    return cidades
