def valida_dados_sessao(chaves):
    """
        Valida se os dados necessarios para o
        funcionamento de um recurso estao salvos
        na sessao
    """
    is_set = True 
    for v in ['cidades', 'dt_inicial', 'dt_final']:
        is_set = v in session    
    if not is_set:
        warning('O período e cidades são obrigatórios.')
        return redirect(url_for('tributacao.logistica_carga_cidades'))
