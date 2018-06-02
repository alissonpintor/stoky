# import das Models
from app.models import WmsColaborador


def buscar_colaboradores_ativos():
    """
        retorna todos os colaboradores ativos
        no WMS
    """
    colaboradores = WmsColaborador.query.filter(
        WmsColaborador.ativo == 'S'
    ).order_by(
        WmsColaborador.nome
    )

    return colaboradores