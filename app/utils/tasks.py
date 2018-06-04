# imports do flask
from flask_weasyprint import HTML, render_pdf
from flask import render_template
from datetime import datetime
import cups
import redis

# importa o Celery
from celery.schedules import crontab
from app import app
from app import mycelery
from app import db

# import das models usadas na view
from app.models import AppConfig, WmsViewRomaneioSeparacao

key = 'a8f5f167f44f4964e6c998dee827110c'

@mycelery.task(name='imprimir_romaneio_onda')
def imprimir_romaneio_onda():
    # cria o mecanismo de bloqueio
    REDIS_CLIENT = redis.Redis()
    timeout = 60 * 5 #  expira em 5min
    locked = False
    lock = REDIS_CLIENT.lock(key, timeout=timeout)
    
    try:
        # tenta adiquirir o bloqueio da tarefa
        locked = lock.acquire(blocking=False)
        
        # se o bloqueio foi bem sucedido executa a tarefa
        if locked:
            config = buscar_dthr_ultima_onda()
            if not config or not config.dthr_ultima_onda:
                return

            onda = busar_romaneio_separacao(config.dthr_ultima_onda, first=True)
            if not onda:
                return
            ondas = busar_romaneio_separacao(config.dthr_ultima_onda)
            
            ultima_hora = config.dthr_ultima_onda
            for i, onda in enumerate(ondas):
                if i == 1:
                    ultima_hora = onda.dthr_geracao
                
                if ultima_hora < onda.dthr_geracao:
                    ultima_hora = onda.dthr_geracao
                
                with app.test_request_context('/'):
                    html = template_romaneio_separacao(onda)
                    pdf = HTML(string=html).write_pdf()
                    
                    f = open('saida.pdf', 'wb')
                    f.write(pdf)
                    f.close()

                    default_printer = 'L655'
                    conn = cups.Connection()
                    printers = conn.getPrinters()

                    if default_printer in printers.keys():
                        conn.printFile(default_printer, 'saida.pdf', 'Romaneio Separacao Onda', {})
            
            if ultima_hora:
                config.dthr_ultima_onda = ultima_hora
                db.session.add(config)
                db.session.commit()
    finally:
        print('Recurso Liberado')

        # libera o bloqueio da tarefa
        if locked:
            lock.release()

mycelery.conf.beat_schedule = {
    # Executa a impressao dos romaneios das 
    # ondas a cada 10 segundos
    'add-impressao': {
        'task': 'imprimir_romaneio_onda',
        'schedule': 10.0,
    },
}


def buscar_dthr_ultima_onda():
    """
        busca a ultima data e hora dos
        romaneios impressos
    """
    config = AppConfig.query.filter_by(config_id=1).first()
    return config


def busar_romaneio_separacao(dthr_geracao, first=False):
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
        WmsViewRomaneioSeparacao.unidade_medida,
        WmsViewRomaneioSeparacao.dthr_geracao
    ).filter(
        WmsViewRomaneioSeparacao.dthr_geracao > dthr_geracao
    )

    if first:
        onda = onda.first()
    else:
        onda = onda.all()

    return onda


def template_romaneio_separacao(onda):
    """
        gera em HTML para o pdf
    """
    
    template = 'wmserros/reports/report-romaneio-separacao.html'
    datahora = datetime.now().strftime('%d/%m/%Y %H:%M')

    result = {
        'title': 'Relatorio Romaneio de Separação',
        'onda': onda,
        'datahora': datahora
    }
    
    html =  render_template(template, **result)    
    return html