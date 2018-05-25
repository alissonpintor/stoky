from flask import flash


def success(message):
    """ Grava uma mensagem de sucesso para o Usuario usando o flash """
    content = {'type': 'success', 'content': message}                
    flash(content)


def info(message):
    """ Grava uma mensagem de informação para o Usuario usando o flash """
    content = {'type': 'info', 'content': message}                
    flash(content)


def warning(message):
    """ Grava uma mensagem de aviso para o Usuario usando o flash """
    content = {'type': 'warning', 'content': message}                
    flash(content)


def error(message):
    """ Grava uma mensagem de erro para o Usuario usando o flash """
    content = {'type': 'error', 'content': message}            
    flash(content)