from app import app, db, logistica_permission
from flask import render_template, abort, make_response, session
from flask import request, redirect, url_for, flash, make_response
from flask_login import login_required
from flask import jsonify
from flask.json import dumps
import flask_excel as excel
from flask_mail import Message
from flask_weasyprint import HTML, render_pdf

from datetime import datetime, date
import calendar
import dateparser

import math

from sqlalchemy.orm import exc
from sqlalchemy import exc as core_exc

# variavel com o Blueprint
from . import wmserros

# import app
from .. import mail

from app.shared.colors import Color
from app.shared.charts import BaseChart, Data, Dataset, LineChart

# Classes Models de Wms Erros
from ..models import Tarefas, Erros, RegistroDeErros, WmsOnda, WmsColaborador
from ..models import WmsItems, WmsSeparadoresTarefas, PontuacaoMetaLogistica
from ..models import MetaTarefa, ParametrosMetas, WmsTarefasCd, WmsPredio, WmsRegiaoSeparacao
from ..models import ViewSaldoProduto, ViewProduto, WmsEstoqueCd, EstoqueSaldo, StokyMetasView
from app.models import WmsViewRomaneioSeparacao

# Formularios
from .forms import TarefasForm, ErrosForm, BuscarMetasForm
from .forms import ParametrosForm, BuscarPeriodoForm, FormRomaneioSeparacao

# import das buscas na base de dados
from .data import buscar_colaboradores_ativos

# import dos utils
from app.utils.messages import success, warning, info, error

TABLES = {'tarefas': {'classe': Tarefas, 'url_padrao': 'wmserros.tarefas'},
          'erros': {'classe': Erros, 'url_padrao': 'wmserros.erros'},
          'parametros': {'classe': ParametrosMetas, 'url_padrao': 'wmserros.parametros'}}

def format_date(userdate):
    date = dateparser.parse(userdate, date_formats=['%Y-%m-%d'])
    try:
        return datetime.strftime(date)
    except TypeError:
        return None

'''
@wmserros.route("/export", methods=['GET'])
def docustomexport():
    query_sets = WmsColaborador.query.order_by('nome').all()
    column_names = ['id', 'nome']
    return excel.make_response_from_query_sets(query_sets, column_names, "xlsx", file_name='rel.xlsx')
'''

# ROTA USADA PARA DELETAR OS REGISTROS
@wmserros.route('/deletar/<path>/<id>')
@login_required
@logistica_permission.require(http_exception=401)
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


def delete(klass, id):
    """
        delete o registro da base de dados 
    """
    data = klass.by_id(id)
    if not data:
        error('Nao foi possivel excluir. Registro não existe')
    else:
        data = data.delete()
        message = success if data.status else error
        message(data.message)


@wmserros.route('/parametros', methods=['GET', 'POST'])
@wmserros.route('/parametros/<id>')
@login_required
@logistica_permission.require(http_exception=401)
def parametros(id=None):
    template = 'wmserros/view_parametros.html'
    parametros = ParametrosMetas.all()
    
    colaboradores = buscar_colaboradores_ativos()
    choices = [(c.id, '{0:0>2} - {1}'.format(c.id, c.nome)) for c in colaboradores]
    choices.insert(0, (0, ''))

    form = ParametrosForm()
    form.colaboradores_excluidos.choices = choices

    import cups
    conn = cups.Connection()
    conn.printTestPage('L655')

    if form.validate_on_submit():
        parametro = ParametrosMetas()
        if form.id.data:
            parametro = ParametrosMetas.by_id(form.id.data)

        parametro.descricao = form.descricao.data
        parametro.valor_meta_diario = form.valor_meta_diario.data

        excluidos = form.colaboradores_excluidos.data
        excluidos = '-'.join([str(id) for id in excluidos])
        parametro.colaboradores_excluidos = excluidos
        
        parametro = parametro.update()
        message = success if parametro.status else error
        message(parametro.message)

        return redirect(url_for('wmserros.parametros'))

    if id:
        parametro = ParametrosMetas.by_id(id)
        excluidos = parametro.colaboradores_excluidos
        excluidos = [int(id) for id in excluidos.split('-')]
        
        form.id.data = parametro.id
        form.descricao.data = parametro.descricao
        form.colaboradores_excluidos.data = excluidos
        form.valor_meta_diario.data = parametro.valor_meta_diario
    
    result = {
        'form': form,
        'parametros': parametros
    }
    return render_template(template, **result)


@wmserros.route('/parametros/delete/<int:id>')
@login_required
@logistica_permission.require(http_exception=401)
def parametros_delete(id=None):    
    if id:
        delete(ParametrosMetas, id)
    return redirect(url_for('wmserros.parametros'))


@wmserros.route('/tarefas', methods=['GET', 'POST'])
@wmserros.route('/tarefas/<id>')
@login_required
@logistica_permission.require(http_exception=401)
def tarefas(id=None):
    template = 'wmserros/view_tarefas.html'
    tarefas = Tarefas.all()
    form = TarefasForm()
    classe = 'tarefas'

    if form.validate_on_submit():
        tarefa = Tarefas()
        
        if form.id_tarefa.data:
            tarefa = Tarefas.by_id(form.id_tarefa.data)
        
        if not tarefa:
            warning('O registro não existe')
            redirect(url_for('wmserros.tarefas'))
        
        tarefa.descricao = form.nome_tarefa.data
        tarefa.lista_ids_wms = form.lista_ids_wms.data
        tarefa.valor_meta = form.valor_meta.data
        tarefa.flag_meta_variavel = form.flag_meta_variavel.data
        tarefa.qtdade_min_colaborador = form.qtdade_min_colaborador.data

        tarefa = tarefa.update()
        message = success if tarefa.status else error
        message(tarefa.message)

        redirect(url_for('wmserros.tarefas'))

    if id:
        tarefa = Tarefas.by_id(id)

        if tarefa:        
            form.id_tarefa.data = tarefa.id_tarefa
            form.nome_tarefa.data = tarefa.descricao
            form.lista_ids_wms.data = tarefa.lista_ids_wms
            form.valor_meta.data = tarefa.valor_meta
            form.flag_meta_variavel.data = tarefa.flag_meta_variavel
            form.qtdade_min_colaborador.data = tarefa.qtdade_min_colaborador
        
    result = {
        'form': form,
        'tarefas': tarefas,
        'classe': classe
    }
    return render_template(template, **result)


@wmserros.route('/calculo_col_tarefas', methods=['GET', 'POST'])
@login_required
@logistica_permission.require(http_exception=401)
def calculo_col_tarefas():
    form = BuscarPeriodoForm()

    separacao_obj = {'tarefas': 0, 'qtdade_colab': 0, 'regioes': []}
    conferecia_obj = {'tarefas': 0, 'qtdade_colab': 0}

    if form.validate_on_submit():
        tarefas_pendentes = 0
        dt_inicial = dateparser.parse(form.data_inicial.data, date_formats=['%d-%m-%Y'])
        dt_final = dateparser.parse(form.data_final.data + ' 23:00:00', date_formats=['%d-%m-%Y %H:%M:%S'])
        tempo = form.tempo.data

        # Colaboradores necessários para Separação
        separacao = Tarefas.query.filter_by(id_tarefa = 1).first()
        tarefas_por_hora = (separacao.valor_meta / 510) * tempo
        ids_tarefas = [int(id) for id in separacao.lista_ids_wms.split(',')]

        tarefas = WmsTarefasCd.query.filter(WmsTarefasCd.liberada == 'S')
        tarefas = tarefas.filter(WmsTarefasCd.id_tipo_tarefa.in_(ids_tarefas))
        tarefas = tarefas.filter(WmsTarefasCd.data_tarefa.between(dt_inicial, dt_final))

        query = db.session.query(WmsRegiaoSeparacao.descricao, db.func.count(WmsTarefasCd.id_tarefa_cd).label('total'))
        query = query.join(WmsTarefasCd.predio, WmsRegiaoSeparacao)
        query = query.filter(WmsTarefasCd.liberada == 'S')
        query = query.filter(WmsTarefasCd.id_tipo_tarefa.in_(ids_tarefas))
        query = query.filter(WmsTarefasCd.data_tarefa.between(dt_inicial, dt_final))
        query = query.group_by(WmsRegiaoSeparacao.descricao)

        for t in query:
            result = {
                'regiao': t.descricao,
                'qtdade': t.total,
                'colaborador': math.ceil(t.total / tarefas_por_hora)
            }
            separacao_obj['regioes'].append(result)
            tarefas_pendentes += t.total

        separacao_obj['tarefas'] = tarefas.count()
        qtdade_colab = math.ceil(tarefas_pendentes / tarefas_por_hora)
        qtdade_regioes = len(separacao_obj['regioes'])
        separacao_obj['qtdade_colab'] = qtdade_colab if qtdade_colab > qtdade_regioes else qtdade_regioes

        # Colaboradores necessários para Conferencia
        conferencia = Tarefas.query.filter_by(id_tarefa = 2).first()
        tarefas_por_hora = (conferencia.valor_meta / 510) * tempo
        ids_tarefas = [int(id) for id in conferencia.lista_ids_wms.split(',')]

        tarefas = WmsTarefasCd.query.filter(WmsTarefasCd.liberada == 'S')
        tarefas = tarefas.filter(WmsTarefasCd.id_tipo_tarefa.in_(ids_tarefas))
        tarefas = tarefas.filter(WmsTarefasCd.data_tarefa.between(dt_inicial, dt_final))

        conferecia_obj['tarefas'] = tarefas.count()
        conferecia_obj['qtdade_colab'] = math.ceil(tarefas.count() / tarefas_por_hora)


    return render_template('wmserros/view_calculo_col_tarefas.html', form=form, separacao_obj=separacao_obj,\
                            conferecia_obj=conferecia_obj)


@wmserros.route('/exibir_metas', methods=['GET', 'POST'])
@login_required
@logistica_permission.require(http_exception=401)
def exibir_metas():
    form = BuscarMetasForm()

    parametros = ParametrosMetas.query.order_by(ParametrosMetas.descricao).all()
    form.parametros.choices = [(p.id, '{0:0>2} - {1}'.format(p.id, p.descricao)) for p in parametros]
    form.parametros.choices.insert(0, (0, ''))

    meta_colaboradores = {}
    count_tarefas = 0
    pontos_periodo = 0
    media_pontos_periodo = 0
    count_colaborador = 0
    carga_de_trabalho = {'qtdade_necessaria': 0, 'tarefas': []}

    if form.validate_on_submit():
        # Buscamos todas as tarefas cadastradas
        tarefas = Tarefas.query.all()
        param = ParametrosMetas.query.filter(ParametrosMetas.id == form.parametros.data).first()
        colaboradores_excluidos = [int(id) for id in param.colaboradores_excluidos.split('-')]

        colaborador = WmsColaborador.query.filter(~WmsColaborador.id.in_(colaboradores_excluidos))
        colaborador = colaborador.filter(WmsColaborador.ativo == 'S')

        # variaveis usadas para armazenar os dados das metas
        count_colaborador = colaborador.count() # contador de colaboradores
        first_day = dateparser.parse(form.data_inicial.data, date_formats=['%d-%m-%Y']) # data inicial da busca
        last_day = dateparser.parse(form.data_final.data + ' 23:00:00', date_formats=['%d-%m-%Y %H:%M:%S']) # data final da busca

        for c in colaborador:
            meta_colaboradores[c.id] = {
                'id': c.id,
                'colaborador': c.nome,
                'total': {'qtdade': 0, 'p_qtdade': 0, 'erros': 0, 'p_erros': 0, 'pontos': 0}
            }

        for t in tarefas:
            # pega os ids das tarefas do WMS na tarefa selecionada
            id_tarefas = [int(v) for v in t.lista_ids_wms.split(',')]

            # Query que ira conter o total de tarefas realizados por colaborador
            #   VERIFICAR: esta puxando subtarefas
            query = db.session.query(WmsSeparadoresTarefas.idColaborador,\
                                     WmsSeparadoresTarefas.nomeColaborador,\
                                     db.func.count(WmsSeparadoresTarefas.id).label('qtd_tarefas'))

            query = query.filter(WmsSeparadoresTarefas.dataTarefa.between(first_day, last_day))
            query = query.filter(WmsSeparadoresTarefas.idTipoTarefa.in_(id_tarefas))
            query = query.filter(~WmsSeparadoresTarefas.idColaborador.in_(colaboradores_excluidos))

            query = query.group_by(WmsSeparadoresTarefas.idColaborador, WmsSeparadoresTarefas.nomeColaborador)
            query = query.order_by(WmsSeparadoresTarefas.nomeColaborador) # Fim da busca tarefas colaborador

            total_tarefas = WmsSeparadoresTarefas.query
            total_tarefas = total_tarefas.filter(WmsSeparadoresTarefas.idTipoTarefa.in_(id_tarefas))
            total_tarefas = total_tarefas.filter(WmsSeparadoresTarefas.dataTarefa.between(first_day, last_day)).count()
            count_tarefas += total_tarefas
            pontos_periodo += (param.valor_meta_diario / t.valor_meta) * total_tarefas

            days = (last_day-first_day).total_seconds() / 86400
            carga_de_trabalho['qtdade_necessaria'] += (total_tarefas/t.valor_meta) / days
            carga_de_trabalho['tarefas'].append({
                'descricao': t.descricao,
                'qtdade': (total_tarefas/t.valor_meta) / days
            })

            for q in query:
                qtdade_erros = RegistroDeErros.query.filter(RegistroDeErros.id_colaborador == q.idColaborador)
                qtdade_erros = qtdade_erros.filter(RegistroDeErros.data_cadastro.between(first_day.date(), last_day.date()))
                qtdade_erros = qtdade_erros.join(Erros).filter(Erros.id_tarefa == t.id_tarefa).count()

                pontos_tarefa = (param.valor_meta_diario / t.valor_meta)

                p_qtdade = q.qtd_tarefas * pontos_tarefa
                p_erros = qtdade_erros * (pontos_tarefa * 3)
                result = {
                    'qtdade': q.qtd_tarefas,
                    'erros': qtdade_erros,
                    'p_qtdade': p_qtdade,
                    'p_erros': p_erros,
                    'pontos': p_qtdade - p_erros}

                if q.idColaborador in meta_colaboradores:
                    meta_colaboradores[q.idColaborador][t.descricao] = result
                    meta_colaboradores[q.idColaborador]['total']['qtdade'] += q.qtd_tarefas
                    meta_colaboradores[q.idColaborador]['total']['p_qtdade'] += result['p_qtdade']
                    meta_colaboradores[q.idColaborador]['total']['erros'] += qtdade_erros
                    meta_colaboradores[q.idColaborador]['total']['p_erros'] += result['p_erros']
                    meta_colaboradores[q.idColaborador]['total']['pontos'] += result['pontos']

        media_pontos_periodo += pontos_periodo/count_colaborador

    return render_template('wmserros/view_exibir_metas.html', form=form, meta_colaboradores=meta_colaboradores,\
                            media_pontos_periodo=media_pontos_periodo, count_tarefas=count_tarefas,\
                            count_colaborador=count_colaborador, pontos_periodo=pontos_periodo,\
                            carga_de_trabalho=carga_de_trabalho)


@wmserros.route('/erros', methods=['GET', 'POST'])
@wmserros.route('/erros/<id>')
@login_required
@logistica_permission.require(http_exception=401)
def erros(id=None):
    erros = Erros.query.all()
    tarefas = Tarefas.query.all()
    form = ErrosForm()
    form.tarefa.choices = [(t.id_tarefa, t.descricao) for t in tarefas]
    classe = 'erros'

    if form.validate_on_submit():
        erro = Erros()
        if form.id_erro.data:
            erro = Erros.query.filter(Erros.id_erro == form.id_erro).one()
        erro.descricao = form.nome_erro.data
        erro.id_tarefa = form.tarefa.data

        try:
            db.session.add(erro)
            db.session.commit()
            message = {'type': 'success', 'content': 'Registro cadastrado com sucesso'}
            flash(message)
        except Exception as e:
            message = {'type': 'error', 'content': 'Não foi possível realizar o cadastro -- %s' % e}
            flash(message)

        redirect(url_for('wmserros.erros'))

    if id:
        try:
            erro = Erros.query.filter(Erros.id_erro == id).one()
            form.id_erro.data = erro.id_erro
            form.nome_erro.data = erro.descricao
            form.tarefas.default = erro.id_tarefa
        except Exception as e:
            message = {'type': 'warning', 'content': 'Erro ao alterar registro. -- %s' % e}
            flash(message)

    return render_template('wmserros/view_erros.html', form=form, erros=erros, classe=classe)


@wmserros.route('/informar_erros', methods=['GET', 'POST'])
@wmserros.route('/informar_erros/<busca>')
def informar_erros(busca=None):
    tarefas = Tarefas.query.all()

    if request.method == 'POST':
        required_fields = ['onda', 'cliente', 'id-produto', 'descricao-produto', 'tipo-tarefa', 'tipo-erro', 'colaborador']
        form_validate = True
        for field in required_fields:
            if not request.form.get(field):
                form_validate = False

        if form_validate:
            registro = RegistroDeErros()
            registro.id_onda = request.form.get('onda')
            registro.cliente = request.form.get('cliente')
            registro.id_produto = request.form.get('id-produto')
            registro.descricao_produto = request.form.get('descricao-produto')
            registro.id_tarefa = request.form.get('tipo-tarefa')
            registro.id_erro = request.form.get('tipo-erro')
            registro.id_colaborador = request.form.get('colaborador')
            registro.data_cadastro = datetime.now()

            try:
                db.session.add(registro)
                db.session.commit()
                message = {'type': 'success', 'content': 'Registro cadastrado com sucesso'}
                flash(message)
            except Exception as e:
                message = {'type': 'error', 'content': 'Não foi possível realizar o cadastro -- %s' % e}
                flash(message)
        else:
            message = {'type': 'warning', 'content': 'Todos os campos devem ser preenchidos.'}
            flash(message)

        redirect(url_for('wmserros.erros'))

    # Busca o cliente pelo numero da onda ou tarefa
    if busca == 'onda':
        if request.args.get('onda'):
            onda = int(request.args.get('onda'))
            return json_buscar_onda(onda)

    # Busca o produto pelo codigo do mesmo
    if busca == 'produto':
        if request.args.get('id-produto'):
            produto = int(request.args.get('id-produto'))
            return json_buscar_produto(produto)

    # Busca o colaborador da tarefa selecionada
    if busca == 'colaborador':
        if set(['onda', 'id-produto', 'tipo-tarefa']).issubset(request.args.keys()):
            id_onda = int(request.args.get('onda'))
            id_produto = int(request.args.get('id-produto'))
            id_tarefa = int(request.args.get('tipo-tarefa'))
            return json_buscar_colaborador(id_produto, id_onda=id_onda, id_tarefa=id_tarefa)

    # Busca os erros de acordo com a tarefa selecionada
    if busca == 'tarefa':
        if request.args.get('tipo-tarefa'):
            id_tarefa = int(request.args.get('tipo-tarefa'))
            return json_buscar_erros_tarefa(id_tarefa)

    return render_template('wmserros/view_informar_erros.html', tarefas=tarefas)


@wmserros.route('/dashboard')
def dashboard():

    rankings = None  # lista com o ranking dos 3 primeiros por tarefa.
    bloqueadas = None  # Informações de quantidade de separações bloqueadas.
    resumo_tarefas = {}  # Total de tarefas geradas, concluidas e pendentes.
    pagina = request.cookies.get('pagina')  # cookie para definir a proxima página a ser exibida.

    if pagina == 'ranking' or pagina is None:

        tarefas = Tarefas.query.all()
        rankings = []  # Inicia a variavel como uma lista.

        for tarefa in tarefas:
            # Query que ira conter o total de tarefas realizados por colaborador
            ranking = db.session.query(WmsSeparadoresTarefas.nomeColaborador,
                                       db.func.count(WmsSeparadoresTarefas.id).label('qtd_tarefas'))

            # Aplica os filtros da busca
            ranking = ranking.filter(WmsSeparadoresTarefas.dataTarefa >= date.today())
            ranking = ranking.filter(WmsSeparadoresTarefas.idTipoTarefa.in_(tarefa.getIdsTarefa()))

            # agrupa e ordena a busca
            ranking = ranking.group_by(WmsSeparadoresTarefas.nomeColaborador)
            ranking = ranking.order_by(db.desc('qtd_tarefas')).limit(3)

            # verifica se existe algum registro na query antes de usar os dados
            if ranking.first():
                ranking.nome = tarefa.descricao
                rankings.append(ranking)

    if pagina == 'resumo-geral':
        tarefas = Tarefas.query.all()

        total = []
        pendentes = []
        concluidas = []

        for tarefa in tarefas:

            result = db.session.query(db.func.count(WmsTarefasCd.id_tarefa_cd).label('qtdade'))
            result = result.filter(WmsTarefasCd.data_tarefa >= date.today())
            result = result.filter(WmsTarefasCd.id_tipo_tarefa.in_(tarefa.getIdsTarefa()))

            # Pega o total de tarefas por geradas.
            total_result = result.first()
            if total_result and total_result.qtdade:
                total.append({tarefa.descricao: total_result.qtdade})

            # Pega o total de tarefas concluidas.
            concluidas_result = result.filter(WmsTarefasCd.data_fim.isnot(None)).first()
            if concluidas_result and concluidas_result.qtdade:
                concluidas.append({tarefa.descricao: concluidas_result.qtdade})

            # Pega o total de tarefas pendentes.
            pendentes_result = None  # result.filter(WmsTarefasCd.data_fim.is_(None)).first()
            if pendentes_result and pendentes_result.qtdade:
                pendentes.append({tarefa.descricao: pendentes_result.qtdade})

            resumo_tarefas['total'] = total
            resumo_tarefas['concluidas'] = concluidas
            resumo_tarefas['pendentes'] = pendentes

        # Pega a quantidade de tarefas bloqueadas
        bloqueadas = db.session.query(db.func.count(WmsTarefasCd.id_tarefa_cd).label('qtdade'))

        # Filtros necessários para pegar as tarefas bloqueadas
        bloqueadas = bloqueadas.filter_by(liberada='N')
        bloqueadas = bloqueadas.filter(WmsTarefasCd.id_tar_bloqueadora.isnot(None))
        bloqueadas = bloqueadas.filter(WmsTarefasCd.id_tipo_tarefa.in_([4, 7])).first()

    resp = make_response(render_template('wmserros/view_dashboard.html', rankings=rankings, bloqueadas=bloqueadas, resumo=resumo_tarefas))

    # Verifica qual pagina esta sendo retornada e altera o cookie 'pagina'
    # para que na proxima requizição seja retorna a outra pagina
    paginas = ['ranking', 'resumo-geral']

    if pagina and pagina in paginas:
        index = paginas.index(pagina) + 1

        if index < len(paginas):
            resp.set_cookie('pagina', paginas[index])
        else:
            resp.set_cookie('pagina', paginas[0])
    else:
        resp.set_cookie('pagina', paginas[0])

    return resp


@wmserros.route('/charts')
def charts():
    tarefas = Tarefas.query.all()
    labels = []
    results = []

    dataset = Dataset('label', data=[100, 200, 300, 50, 30, 40, 80])
    dataset02 = Dataset('label 02', data=[75, 500, 800, 120, 410, 77, 199])
    data = Data(labels=['a', 'b', 'c', 'd', 'e', 'f', 'g'])
    data.addDataset(dataset)
    data.addDataset(dataset02)

    c = BaseChart('Teste 01', data=data)

    l2 = []
    dt2 = Dataset('label')

    # Teste de envio de email
    msg = Message("Hello",
                  sender=('Alisson Stoky', "alisson.stoky@gmail.com"),
                  recipients=["alissonpintor@gmail.com"])
    msg.body = "testing"
    mail.send(msg)

    for tarefa in tarefas:

        result = db.session.query()
        result = result.add_column(db.func.count(WmsTarefasCd.id_tarefa_cd).label('qtdade'))
        result = result.filter(WmsTarefasCd.data_tarefa >= date.today())
        result = result.filter(WmsTarefasCd.id_tipo_tarefa.in_(tarefa.getIdsTarefa()))

        # Pega o total de tarefas por geradas.
        total_result = result.first()

        result = []
        if total_result and total_result.qtdade:
            labels.append(tarefa.descricao)
            results.append(total_result.qtdade)
            result.append(total_result.qtdade)

            l2.append(tarefa.descricao)
            dt2.addData(total_result.qtdade)

    d2 = Data(labels=l2)
    d2.addDataset(dt2)
    c2 = BaseChart('Tarefas', data=d2, ctype='pie', _id='pieChart')

    import chartjs
    line = chartjs.chart(title = "Comparativo de Vendas", ctype = "Line", width = 640, height = 480)

    currentYear = date.today().year
    pastSales = []
    currentSales = []

    # Define as colunas que vao ser retornadas na consulta em StokyMetasView
    queryPastSales = db.session.query((db.func.sum(StokyMetasView.val_venda) + db.func.sum(StokyMetasView.val_devolucao)).label('valor'))
    # Define os filtros da consulta
    queryPastSales = queryPastSales.filter(StokyMetasView.dt_movimento.between(date(currentYear-1, 1, 1), date(currentYear-1, 12, 31)))
    queryPastSales = queryPastSales.group_by(db.func.month(StokyMetasView.dt_movimento))

    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    dataTotalSales = Data(labels=months)

    line.set_labels(months)

    datasetPastSales = Dataset("Vendas 2016")
    past = []
    for monthSales in queryPastSales:
        datasetPastSales.addData(str(monthSales.valor))
        past.append(monthSales.valor)

    dataTotalSales.addDataset(datasetPastSales)

    line.add_dataset(past)

    # Define as colunas que vao ser retornadas na consulta em StokyMetasView
    queryCurrentSales = db.session.query((db.func.sum(StokyMetasView.val_venda) + db.func.sum(StokyMetasView.val_devolucao)).label('valor'))
    # Define os filtros da consulta
    queryCurrentSales = queryCurrentSales.filter(StokyMetasView.dt_movimento.between(date(currentYear, 1, 1), date(currentYear, 12, 31)))
    queryCurrentSales = queryCurrentSales.group_by(db.func.month(StokyMetasView.dt_movimento))

    datasetCurrentSales = Dataset("Vendas 2017")
    current = []
    for monthSales in queryCurrentSales:
        import locale
        locale.setlocale(locale.LC_ALL, '')
        sale = locale.currency(monthSales.valor, grouping=True)
        print(sale)
        datasetCurrentSales.addData('{:10.2f}'.format(monthSales.valor))
        current.append(monthSales.valor)

    dataTotalSales.addDataset(datasetCurrentSales)
    line.add_dataset(current)

    lineChart = LineChart('Comparativo de Vendas', data=dataTotalSales, _id='lineChart')

    return render_template('wmserros/charts.html', bg=Color.generate(len(labels), 0.8), labels=labels, results=results, charts=c, charts2=c2, lineChart=lineChart, line=line)


@wmserros.route('/pygal')
def pygal():
    import locale
    locale.setlocale(locale.LC_ALL, '')

    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    currentYear = date.today().year

    # Define as colunas que vao ser retornadas na consulta em StokyMetasView
    queryPastSales = db.session.query((db.func.sum(StokyMetasView.val_venda) + db.func.sum(StokyMetasView.val_devolucao)).label('valor'))
    # Define os filtros da consulta
    queryPastSales = queryPastSales.filter(StokyMetasView.dt_movimento.between(date(currentYear-1, 1, 1), date(currentYear-1, 12, 31)))
    queryPastSales = queryPastSales.group_by(db.func.month(StokyMetasView.dt_movimento))
    past = []
    for monthSales in queryPastSales:
        past.append(monthSales.valor)

    # Define as colunas que vao ser retornadas na consulta em StokyMetasView
    queryCurrentSales = db.session.query((db.func.sum(StokyMetasView.val_venda) + db.func.sum(StokyMetasView.val_devolucao)).label('valor'))
    # Define os filtros da consulta
    queryCurrentSales = queryCurrentSales.filter(StokyMetasView.dt_movimento.between(date(currentYear, 1, 1), date(currentYear, 12, 31)))
    queryCurrentSales = queryCurrentSales.group_by(db.func.month(StokyMetasView.dt_movimento))
    current = []
    for monthSales in queryCurrentSales:
        current.append(monthSales.valor)

    import pygal as pl
    from pygal.style import CleanStyle, LightenStyle

    config = pl.Config()
    config.show_legend = True
    config.human_readable = True
    config.value_formatter = lambda x: locale.currency(x, grouping=True)
    config.fill = True

    my_style = LightenStyle('#336676', base_style=CleanStyle)
    bar_chart = pl.HorizontalBar(config, style=my_style)
    bar_chart.title = 'Comparativo de Vendas 2016/2017'
    bar_chart.x_labels = months
    bar_chart.y_labels = [1000000, 2000000, 3000000, 4000000]
    bar_chart.add('Vendas 2016', past)
    bar_chart.add('Vendas 2017', current)

    line_chart = pl.Line()
    line_chart.add('Fibonacci', [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55])
    line_chart.add('Padovan', [1, 1, 1, 2, 2, 3, 4, 5, 7, 9, 12])

    return render_template('wmserros/pygal.html',
                           bar_chart=bar_chart.render_data_uri(),
                           line_chart=line_chart.render_data_uri())


@wmserros.route('/exibir_erros')
@login_required
@logistica_permission.require(http_exception=401)
def exibir_erros():

    limit = request.args.get('limit')
    offset = request.args.get('offset')
    search = request.args.get('search')
    sort = request.args.get('sort')
    order = request.args.get('order')

    r_json = {'total': 0, 'rows': []}

    if request.args.get('total_remove'):
        total = int(request.args.get('total_remove')) + 1
        for t in range(1, total):
            id_registro = request.args.get('id_%i' % t)
            registro = RegistroDeErros.query.filter_by(id_registro=id_registro).first()

            try:
                db.session.delete(registro)
                db.session.commit()
            except Exception:
                return json_error_response()

        json = jsonify()
        json.status_code = 200
        json.status = 'Registro Excluido com sucesso'
        return json

    if(limit and offset):
        registros = db.session.query(RegistroDeErros)

        if search:
            registros = registros.filter(
                RegistroDeErros.cliente.like("%{}%".format(search)))
        if sort:
            if order == 'desc':
                registros = registros.order_by(
                    db.desc(getattr(RegistroDeErros, sort)))
            else:
                registros = registros.order_by(
                    getattr(RegistroDeErros, sort))

        registros = registros.limit(limit)
        registros = registros.offset(offset)

        r_json['total'] = db.session.query(db.func.count(
            RegistroDeErros.id_registro)).first()

        for r in registros:
            r_json['rows'].append({
                'id_registro': r.id_registro,
                'id_onda': r.id_onda,
                'cliente': r.cliente.capitalize(),
                'id_produto': r.id_produto,
                'id_tarefa': r.erro.tarefa.descricao,
                'id_erro': r.erro.descricao,
                'descricao_produto': r.descricao_produto.capitalize(),
                'colaborador': WmsColaborador.query.filter_by(id = r.id_colaborador).first().nome,
                'data_cadastro': str(r.data_cadastro),
            })
        return jsonify(r_json)

    return render_template('wmserros/view_exibir_erros.html')


@wmserros.route('/reports/romaneio-separacao', methods=['GET', 'POST'])
def romaneio_separacao():
    """
        Gera o relatorio de separacao de produtos
        dos itens que a regiao de separacao e feita
        de forma manual
    """
    template = 'wmserros/romaneio-separacao.html'
    form = FormRomaneioSeparacao()

    if form.validate_on_submit():
        onda_id = form.onda_id.data
        onda = busar_romaneio_separacao(onda_id)

        if onda:
            return redirect(url_for('wmserros.relatorio_romaneio_separacao', onda_id=onda_id))
        else:
            warning('A onda informada não possui produtos para gerar romaneio.')
            return redirect(url_for('wmserros.romaneio_separacao'))

    result = {
        'title': 'Romaneio de Separação',
        'form': form
    }
    return render_template(template, **result)


@wmserros.route('/reports/romaneio-separacao-pdf/<onda_id>', methods=['GET'])
def relatorio_romaneio_separacao(onda_id):
    """
        gera em pdf
    """
    template = 'wmserros/reports/report-task.html'
    onda = busar_romaneio_separacao(onda_id)
    datahora = datetime.now().strftime('%d/%m/%Y %H:%M')

    if not onda:
        warning('A onda informada não possui produtos para gerar romaneio.')
        return redirect(url_for('wmserros.romaneio_separacao'))

    result = {
        'title': 'Relatorio Romaneio de Separação',
        'onda': onda,
        'datahora': datahora
    }
    html =  render_template(template, **result)
    
    pdf = HTML(string=html).write_pdf()
    f = open('saida.pdf', 'wb')
    f.write(pdf)
    f.close()

    import cups
    conn = cups.Connection()
    conn.printFile('ImpConf02', 'saida.pdf', 'teste', {})

    return render_pdf(HTML(string=html))


@wmserros.route('/reports/romaneio-separacao-pdf/<onda_id>', methods=['GET'])
def impressao_romaneio_separacao(onda):
    """
        gera em pdf
    """
    template = 'wmserros/reports/report-task.html'
    datahora = datetime.now().strftime('%d/%m/%Y %H:%M')

    result = {
        'title': 'Relatorio Romaneio de Separação',
        'onda': onda,
        'datahora': datahora
    }
    
    html =  render_template(template, **result)
    
    pdf = HTML(string=html).write_pdf()
    f = open('saida.pdf', 'wb')
    f.write(pdf)
    f.close()

    import cups
    conn = cups.Connection()
    conn.printFile('ImpConf02', 'saida.pdf', 'Romaneio Separacao Onda', {})

    return render_pdf(HTML(string=html))


def json_buscar_onda(id_onda):
    """
    Função usada para buscar o cliente pelo numero da Onda no WMS
    """
    onda = WmsOnda.query.filter_by(id=id_onda).first()
    if onda:
        return jsonify(onda.nomeCliente)
    else:
        return json_buscar_tarefa(id_onda)


def json_buscar_tarefa(id_tarefa):
    """
    Função usada para buscar a tarefa pelo numero da Tarefa no WMS
    """
    tarefa = WmsSeparadoresTarefas.query.filter_by(id=id_tarefa).first()
    if tarefa:
        return jsonify('TAREFA')
    else:
        return json_error_response()


def json_buscar_produto(id_produto):
    """
    Função usada para buscar o produto pelo id do produto no WMS
    """
    produto = WmsItems.query.filter(WmsItems.idCiss == id_produto).first()
    if produto:
        return jsonify(produto.descricao)
    else:
        return json_error_response()


def json_buscar_colaborador(id_produto, id_onda=None, id_tarefa=None):
    tarefas = Tarefas.query.filter(Tarefas.id_tarefa == id_tarefa).first()
    id_tarefas = [int(v) for v in tarefas.lista_ids_wms.split(',')]

    colaborador = db.session.query(WmsSeparadoresTarefas.idColaborador,
                                   WmsSeparadoresTarefas.nomeColaborador)
    colaborador = colaborador.filter_by(idOnda=id_onda)
    colaborador = colaborador.filter_by(idProduto=id_produto)
    colaborador = colaborador.filter(WmsSeparadoresTarefas.idTipoTarefa.in_(id_tarefas))

    if colaborador.count() > 1:
        objs = [{'id': c.idColaborador, 'nome': c.nomeColaborador} for c in colaborador]
        return jsonify(objs)

    elif colaborador.count() == 1:
        c = colaborador.first()
        obj = [{'id': c.idColaborador, 'nome': c.nomeColaborador}]
        return jsonify(obj)

    else:
        colaboradores = WmsColaborador.query.all()
        objs = [{'id': c.id, 'nome': c.nome} for c in colaboradores]
        return jsonify(objs)


def json_buscar_erros_tarefa(id_tarefa):
    """
    Função usada para buscar o produto pelo id do produto no WMS
    """
    erros = Erros.query.filter_by(id_tarefa=id_tarefa)
    if erros.first():
        json = [{'id': e.id_erro, 'descricao': e.descricao} for e in erros]
        return json_response(obj=json)
    else:
        return json_error_response()

def json_response(obj=None):
    if obj:
        json = jsonify(obj)
        return json

def json_error_response(error_code=500):
    json = jsonify()
    json.status_code = error_code
    return json

# RELATORIOS
@wmserros.route("/export", methods=['GET'])
@login_required
@logistica_permission.require(http_exception=401)
def export():
    query = db.session.query(EstoqueSaldo.id_subproduto, ViewProduto.descricao,\
                             ViewProduto.fabricante, EstoqueSaldo.qtd_atual)
    query = query.join(ViewProduto, (db.and_(EstoqueSaldo.id_produto == ViewProduto.id_produto,
                                          EstoqueSaldo.id_subproduto == ViewProduto.id_subproduto)))
    query = query.filter(ViewProduto.flag_inativo == 'F')
    query = query.filter(EstoqueSaldo.id_estoque == 1)

    #query_sets = ViewProduto.query.filter_by(flag_inativo = 'F').order_by(ViewProduto.descricao)[:5]
    result = []
    column_names = ['COD', 'DESCRICAO', 'MARCA', 'QTDADE_CISS', 'QTDADE_WMS']
    result.append(column_names)

    for q in query:
        qtd_wms = db.session.query(db.func.sum(WmsEstoqueCd.qtdade).label('qtd'))
        qtd_wms = qtd_wms.filter(WmsEstoqueCd.id_produto == str(q.id_subproduto)).first()
        qtd_wms = qtd_wms.qtd if qtd_wms.qtd else 0

        if qtd_wms != q.qtd_atual:
            produto = []
            produto.append(q.id_subproduto)
            produto.append(q.descricao)
            produto.append(q.fabricante)
            produto.append(q.qtd_atual)
            produto.append(qtd_wms)

            result.append(produto)

    return excel.make_response_from_array(result, "xlsx", file_name='rel.xlsx')


def busar_romaneio_separacao(onda_id):
    """
        busca a onda com os produtos que
        fazem separacao manual
    """
    onda = db.session.query(
        WmsViewRomaneioSeparacao.onda_onda_id,
        WmsViewRomaneioSeparacao.num_pedido,
        WmsViewRomaneioSeparacao.nome_cliente,
        WmsViewRomaneioSeparacao.dt_emissao,
        WmsViewRomaneioSeparacao.cidade,
        WmsViewRomaneioSeparacao.observacao,
        WmsViewRomaneioSeparacao.cod_ciss,
        WmsViewRomaneioSeparacao.descricao,
        WmsViewRomaneioSeparacao.qtd,
        WmsViewRomaneioSeparacao.unidade_medida
    ).filter_by(
        onda_onda_id=int(onda_id)
    ).all()

    return onda
