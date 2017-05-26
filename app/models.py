
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager, app

# MODELS DO FLASK_LOGIN#######################################################
class User(UserMixin, db.Model):
    """
    Create an User table
    """

    # Ensures table will be named in plural and not in singular
    # as is the name of the model
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(60), index=True, unique=True)
    username = db.Column(db.String(60), index=True, unique=True)
    first_name = db.Column(db.String(60), index=True)
    last_name = db.Column(db.String(60), index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    is_admin = db.Column(db.Boolean, default=False)

    @property
    def password(self):
        """
        Prevent pasword from being accessed
        """
        raise AttributeError('password is not a readable attribute.')

    @password.setter
    def password(self, password):
        """
        Set password to a hashed password
        """
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """
        Check if hashed password matches actual password
        """
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<Employee: {}>'.format(self.username)

class Role(db.Model):
    """
    Create a Role table
    """

    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True)
    description = db.Column(db.String(200))
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role: {}>'.format(self.name)

# Set up user_loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# MODELS DO CISS ##############################################################
class ClienteFornecedor(db.Model):
    __bind_key__ = 'ciss'
    __tablename__ = 'CLIENTE_FORNECEDOR'
    id_cli_for = db.Column('IDCLIFOR', db.Integer, primary_key=True)
    nome = db.Column('NOME', db.String(80), nullable=False)
    uf_cli_for = db.Column('UFCLIFOR', db.String(2))

class ConfereAutoriza(db.Model):
    __bind_key__ = 'ciss'
    __tablename__ = 'CONFERE_AUTORIZA'
    id_aut = db.Column('IDAUTORIZACAO', db.Integer, primary_key=True)
    id_empresa = db.Column('IDEMPRESA', db.Integer, primary_key=True)
    num_nota = db.Column('NUMNOTA', db.Integer, primary_key=True)
    serie_nota = db.Column('SERIENOTA', db.String(3), primary_key=True)
    id_fornecedor = db.Column('IDCLIFOR', db.ForeignKey('CLIENTE_FORNECEDOR.IDCLIFOR'), primary_key=True)

    fornecedor = db.relationship('ClienteFornecedor', backref=db.backref('id_fornecedor'))

class Ncm(db.Model):
    __bind_key__ = 'ciss'
    __tablename__ = 'NCM'
    ncm = db.Column('NCM', db.String(8), primary_key=True)
    descricao = db.Column('DESCRICAO', db.String(820))
    flag_carga_media = db.Column('FLAGCARGATRIBUTARIAMEDIA', db.String(1), db.CheckConstraint("flag_carga_media=='T' or flag_carga_media=='F'"))

class Produto(db.Model):
    __bind_key__ = 'ciss'
    __tablename__ = 'PRODUTO'
    id_produto = db.Column('IDPRODUTO', db.Integer, primary_key=True)
    descricao = db.Column('DESCRCOMPRODUTO', db.String(60))
    fabricante = db.Column('FABRICANTE', db.String(40))
    per_ipi = db.Column('PERIPI', db.Integer)
    per_ipi_saida = db.Column('PERIPISAIDA', db.Integer)
    id_cst_ipi_entrada = db.Column('IDCSTIPIENTRADA', db.Integer)
    id_cst_ipi_saida = db.Column('IDCSTIPISAIDA', db.Integer)
    id_eqp_entrada = db.Column('IDCODENQIPIENTRADA', db.Integer)
    id_eqp_saida = db.Column('IDCODENQIPISAIDA', db.Integer)
    flag_trib_grupo = db.Column('FLAGTRIBUTACAOGRUPO', db.String(1), db.CheckConstraint("flag_trib_grupo=='T' or flag_trib_grupo=='F'"))

class ProdutoGrade(db.Model):
    __bind_key__ = 'ciss'
    __tablename__ = 'PRODUTO_GRADE'
    id_subproduto = db.Column('IDSUBPRODUTO', primary_key=True)
    id_produto_id = db.Column('IDPRODUTO', db.ForeignKey('PRODUTO.IDPRODUTO'), primary_key=True)
    sub_descricao = db.Column('SUBDESCRICAO', db.String(100), nullable=False)
    flag_inativo = db.Column('FLAGINATIVO', db.String(1), db.CheckConstraint("flag_inativo=='T' or flag_inativo=='F'"))
    num_ncm = db.Column('NCM', db.ForeignKey('NCM.NCM'))

    produto = db.relationship('Produto', backref=db.backref('id_produto_id'))
    ncm = db.relationship('Ncm', backref=db.backref('num_ncm'))
    confere_mercadoria = db.relationship('ConfereMercadoria',
                                          primaryjoin="and_(ProdutoGrade.id_produto_id == ConfereMercadoria.id_produto, "
                                                            "ProdutoGrade.id_subproduto == ConfereMercadoria.id_subproduto)",
                                          backref='produto_grade_confere')
    produto_tributacao = db.relationship('ProdutoTributacao',
                                          primaryjoin="and_(ProdutoGrade.id_produto_id == ProdutoTributacao.id_produto, "
                                                            "ProdutoGrade.id_subproduto == ProdutoTributacao.id_subproduto)",
                                          backref='produto_grade_tributacao')

class EstoqueSaldo(db.Model):
    __bind_key__  = 'ciss'
    __tablename__ = 'ESTOQUE_SALDO_ATUAL'
    id_produto = db.Column('IDPRODUTO', db.ForeignKey('PRODUTOS_VIEW.IDPRODUTO'), primary_key=True)
    id_subproduto = db.Column('IDSUBPRODUTO', db.ForeignKey('PRODUTOS_VIEW.IDSUBPRODUTO'), primary_key=True)
    id_estoque = db.Column('IDLOCALESTOQUE', db.Integer, primary_key=True)
    id_empresa = db.Column('IDEMPRESA', db.Integer, primary_key=True)
    qtd_atual = db.Column('QTDATUALESTOQUE', db.Numeric(10,2))

    v_produto = db.relationship('ViewProduto',
                                primaryjoin="and_(EstoqueSaldo.id_produto == ViewProduto.id_produto, "
                                            "EstoqueSaldo.id_subproduto == ViewProduto.id_subproduto)")

class ConfereMercadoria(db.Model):
    __bind_key__ = 'ciss'
    __tablename__ = 'CONFERE_MERCADORIA'
    id_autorizacao = db.Column('IDAUTORIZACAO', db.ForeignKey('CONFERE_AUTORIZA.IDAUTORIZACAO'), primary_key=True)
    id_produto = db.Column('IDPRODUTO', db.ForeignKey('PRODUTO_GRADE.IDPRODUTO'), primary_key=True)
    id_subproduto = db.Column('IDSUBPRODUTO', db.ForeignKey('PRODUTO_GRADE.IDSUBPRODUTO'), primary_key=True)

    autorizacao = db.relationship('ConfereAutoriza', backref=db.backref('id_autorizacao'))

class ProdutoTributacao(db.Model):
    __bind_key__ = 'ciss'
    __tablename__ = 'PRODUTO_TRIBUTACAO_ESTADO'
    uf = db.Column('UF', db.String(2), primary_key=True)
    id_produto = db.Column('IDPRODUTO', db.ForeignKey('PRODUTO_GRADE.IDPRODUTO'), primary_key=True)
    id_subproduto = db.Column('IDSUBPRODUTO', db.ForeignKey('PRODUTO_GRADE.IDSUBPRODUTO'), primary_key=True)
    per_icms_ent = db.Column('PERICMENT', db.Integer())
    per_icms_subst = db.Column('PERICMSUBST', db.Integer())
    per_margem_subst = db.Column('PERMARGEMSUBSTI', db.Integer())
    per_margem_original = db.Column('PERMARGEMSUBSTISAI', db.Integer())
    id_sit_trib = db.Column('IDSITTRIBENT', db.Integer())
    tipo_trib_ent = db.Column('TIPOSITTRIBENT', db.Integer())

class ViewProduto(db.Model):
    __bind_key__ = 'ciss'
    __tablename__ = 'PRODUTOS_VIEW'
    id_produto = db.Column('IDPRODUTO', db.Integer, primary_key=True)
    id_subproduto = db.Column('IDSUBPRODUTO', db.Integer, primary_key=True)
    descricao = db.Column('DESCRICAOPRODUTO', db.String(100))
    fabricante = db.Column('FABRICANTE', db.String(50))
    flag_inativo = db.Column('FLAGINATIVO', db.String(1), db.CheckConstraint("flag_inativo=='T' or flag_inativo=='F'"))

class ViewSaldoProduto(db.Model):
    __bind_key__ = 'ciss'
    __tablename__ = 'PRODUTOS_SALDOS_VIEW'
    id_produto = db.Column('IDPRODUTO', db.ForeignKey('PRODUTOS_VIEW.IDPRODUTO'), primary_key=True)
    id_subproduto = db.Column('IDSUBPRODUTO', db.ForeignKey('PRODUTOS_VIEW.IDSUBPRODUTO'), primary_key=True)
    id_empresa = db.Column('IDEMPRESA', db.Integer, primary_key=True)
    qtd_atual = db.Column('QTDATUALESTOQUE', db.Numeric(10,2))
    qtd_disponivel = db.Column('QTDDISPONIVEL', db.Numeric(10,2))
    qtd_reserva = db.Column('QTDSALDORESERVA', db.Numeric(10,2))

    v_produto = db.relationship('ViewProduto',
                                primaryjoin="and_(ViewSaldoProduto.id_produto == ViewProduto.id_produto, "
                                            "ViewSaldoProduto.id_subproduto == ViewProduto.id_subproduto)",
                                backref=db.backref('v_produto_saldo'))



"""
################################################################################
MODELS DO APP METAS ------------------------------------------------------------
################################################################################
"""

# MODELS DO APP ----------------------------------------------------------------
vendedor_identifier = db.Table('tbl_vendedor_identifier',
    db.Column('id_vendedor', db.Integer, db.ForeignKey('tbl_vendedores.id_vendedor')),
    db.Column('id_grupo', db.Integer, db.ForeignKey('tbl_grupo_de_vendedores.id_grupo'))
)

class AssMetasVendedor(db.Model):
    __tablename__ = 'tbl_metas_vendedor'
    id_meta_id = db.Column(db.Integer, db.ForeignKey('tbl_meta_vendas.id_meta'), primary_key=True)
    id_vendedor_id = db.Column(db.Integer, db.ForeignKey('tbl_vendedores.id_vendedor'), primary_key=True)
    val_meta_min_vendedor = db.Column(db.Numeric(10,2), db.CheckConstraint('val_meta_min_vendedor>0'))
    val_meta_vendedor = db.Column(db.Numeric(10,2), db.CheckConstraint('val_meta_vendedor>0'), nullable=False)

    meta = db.relationship('MetaVendas', back_populates="vendedores")
    vendedor = db.relationship('Vendedor', back_populates="metas")

class Vendedor(db.Model):
    __tablename__ = 'tbl_vendedores'
    id_vendedor = db.Column(db.Integer, primary_key=True)
    id_vendedor_ciss = db.Column(db.Integer, unique=True)
    nome_vendedor = db.Column(db.String(120), nullable=False)
    flag_inativo = db.Column(db.Boolean)

    metas = db.relationship("AssMetasVendedor", back_populates="vendedor")

class GruposDeVendedores(db.Model):
    __tablename__ = 'tbl_grupo_de_vendedores'
    id_grupo = db.Column(db.Integer, primary_key=True)
    nome_grupo = db.Column(db.String(120), nullable=False)
    vendedores = db.relationship('Vendedor', secondary=vendedor_identifier)

class MetaVendas(db.Model):
    __tablename__ = 'tbl_meta_vendas'
    id_meta = db.Column(db.Integer, primary_key=True)
    nome_meta = db.Column(db.String(120), nullable=False, unique=True)
    dt_inicial = db.Column(db.Date(), nullable=False)
    dt_final = db.Column(db.Date(), nullable=False)
    valor_meta_minimo = db.Column(db.Numeric(10,2), db.CheckConstraint('valor_meta_minimo>0'))
    valor_meta = db.Column(db.Numeric(10,2), db.CheckConstraint('valor_meta>0'))
    #flag_inativo = db.Column(db.Boolean)

    vendedores = db.relationship('AssMetasVendedor', back_populates="meta", cascade="save-update, merge, delete, delete-orphan")

class MetaPromocional(db.Model):
    __tablename__ = 'tbl_meta_promocional'
    id_meta = db.Column(db.Integer, primary_key=True)
    nome_meta = db.Column(db.String(120), nullable=False, unique=True)
    dt_inicial = db.Column(db.Date(), nullable=False)
    dt_final = db.Column(db.Date(), nullable=False)
    valor_meta = db.Column(db.Numeric(10,2), db.CheckConstraint('valor_meta>0'))
    qtdade_meta = db.Column(db.Integer, db.CheckConstraint('qtdade_meta>0'))
    id_grupo_id = db.Column(db.Integer, db.ForeignKey('tbl_grupo_de_vendedores.id_grupo'))
    id_fabricante = db.Column(db.Integer)

    grupo = db.relationship('GruposDeVendedores', backref=db.backref('id_grupo_id'))

# MODELS DO CISS ---------------------------------------------------------------
class Empresa(db.Model):
    __bind_key__ = 'ciss'
    __tablename__ = 'EMPRESA'
    id = db.Column('IDEMPRESA', db.Integer, primary_key=True)
    descricao = db.Column('NOMEFANTASIA', db.String(120))

class Marcas(db.Model):
    __bind_key__ = 'ciss'
    __tablename__ = 'MARCA'
    id = db.Column('IDMARCAFABRICANTE', db.Integer, primary_key=True)
    descricao = db.Column('DESCRICAO', db.String(100))

class StokyMetasView(db.Model):
    __bind_key__ = 'ciss'
    __tablename__ = 'STOKY_METAS'
    id_planilha = db.Column('IDPLANILHA', db.Integer, primary_key=True)
    id_empresa = db.Column('IDEMPRESA', db.Integer, db.ForeignKey('EMPRESA.IDEMPRESA'), primary_key=True)
    id_sequencia = db.Column('NUMSEQUENCIA', db.Integer, primary_key=True)
    id_vendedor = db.Column('IDVENDEDOR', db.Integer, db.ForeignKey('CLIENTE_FORNECEDOR.IDCLIFOR'), nullable=False)
    dt_movimento = db.Column('DTMOVIMENTO', db.Date())
    id_produto = db.Column('IDSUBPRODUTO', db.Integer, db.ForeignKey('PRODUTOS_VIEW.IDSUBPRODUTO'), nullable=False)
    id_marca = db.Column('IDMARCAFABRICANTE', db.Integer, db.ForeignKey('MARCA.IDMARCAFABRICANTE'))
    val_venda = db.Column('VENDA', db.Numeric(10, 2))
    val_devolucao = db.Column('DEVOLUCAO', db.Numeric(10, 2))
    val_lucro = db.Column('LUCRO', db.Numeric(10, 2))

    #empresa = db.relationship('Empresa', backref=db.backref('id_empresa', order_by=id_empresa))
    vendedor = db.relationship("ClienteFornecedor", backref=db.backref('id_vendedor', order_by=id_vendedor))
    produto = db.relationship('ViewProduto', backref=db.backref('meta', order_by=id_produto))
    marca = db.relationship('Marcas', backref=db.backref('id_marca', order_by=id_marca))

"""
################################################################################
MODELS DO APP WMSERROS ---------------------------------------------------------
################################################################################
"""

# MODELS DO APP ----------------------------------------------------------------
class Tarefas(db.Model):
    __tablename__ = 'tbl_tarefas'
    id_tarefa = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)
    lista_ids_wms = db.Column(db.String(100), nullable=False)
    valor_meta = db.Column(db.Float, nullable=False)
    qtdade_min_colaborador = db.Column(db.Integer, default=1)
    flag_meta_variavel = db.Column(db.Boolean, default=False)

class PontuacaoMetaLogistica(db.Model):
    __tablename__ = 'tbl_meta_logistica'
    id_meta = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)
    valor_meta = db.Column(db.Float, nullable=False)

class ParametrosMetas(db.Model):
    __tablename__ = 'tbl_paramtros_metas'
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(30), nullable=False)
    colaboradores_excluidos = db.Column(db.String(100), nullable=False)
    valor_meta_diario = db.Column(db.Float, nullable=False)

class MetaTarefa(db.Model):
    __tablename__ = 'tbl_meta_tarefa'
    id_meta = db.Column(db.Integer, primary_key=True)
    valor_meta = db.Column(db.Float, nullable=False)
    id_tarefa = db.Column(db.Integer, db.ForeignKey('tbl_tarefas.id_tarefa'), nullable=False)

    tarefas = db.relationship('Tarefas', backref=db.backref('id_pontuacao'))

class Erros(db.Model):
	__tablename__ = 'tbl_erros'
	id_erro = db.Column(db.Integer, primary_key=True)
	descricao = db.Column(db.String(100), nullable=False)
	id_tarefa = db.Column(db.Integer, db.ForeignKey('tbl_tarefas.id_tarefa'), nullable=False)

	tarefa = db.relationship("Tarefas", backref=db.backref('id_erro', order_by=descricao))

class RegistroDeErros(db.Model):
	__tablename__ = 'tbl_registro_de_erros'
	id_registro = db.Column(db.Integer, primary_key=True)
	id_onda = db.Column(db.Integer, nullable=False)
	id_tarefa = db.Column(db.Integer, nullable=True)
	cliente = db.Column(db.String(100), nullable=False)
	id_produto = db.Column(db.String(10), nullable=False)
	id_erro = db.Column(db.Integer, db.ForeignKey('tbl_erros.id_erro'),nullable=False)
	descricao_produto = db.Column(db.String(100), nullable=False)
	id_colaborador = db.Column(db.Integer, nullable=True)
	data_cadastro = db.Column(db.Date())

	erro = db.relationship("Erros", backref=db.backref('id_registro', order_by=id_colaborador))

# MODELS DO FULLWMS ---------------------------------------------------------------
class WmsOnda(db.Model):
    __bind_key__ = 'wms'
    __tablename__ = 'STOKY_ONDAS_POR_CLIENTE'
    id = db.Column('ONDA_ID', db.Integer, primary_key=True)
    idPedido = db.Column('PEDIDO_ID', db.Integer)
    idCiss = db.Column('NUM_PEDIDO', db.String(10))
    nomeCliente = db.Column('NOME_CLIENTE', db.String(100))

class WmsColaborador(db.Model):
    __bind_key__ = 'wms'
    __tablename__ = 'WMS_COLABORADORES'
    id = db.Column('COD_COLAB', db.Integer, primary_key=True)
    nome = db.Column('NOME', db.String(100))
    ativo = db.Column('ATIVO', db.String(1), db.CheckConstraint("ativo == 'S' or ativo == 'N'"))

class WmsItems(db.Model):
    __bind_key__ = 'wms'
    __tablename__ = 'ITEM'
    id = db.Column('ID', db.Integer, primary_key=True)
    idCiss = db.Column('CODIGO', db.String(10))
    descricao = db.Column('DESCRICAO', db.String(100))

class WmsRegiaoSeparacao(db.Model):
    __bind_key__ = 'wms'
    __tablename__ = 'WMS_REGIOES_SEPARACOES'
    id_regiao = db.Column('COD_REGSEP', db.Integer, primary_key=True)
    id_empresa = db.Column('EMPR_CODEMP', db.Integer, primary_key=True)
    descricao = db.Column('DESCRICAO', db.String(50))

class WmsEstoqueCd(db.Model):
    __bind_key__  = 'wms'
    __tablename__ = 'WMS_ESTOQUES_CD'
    id_estoque = db.Column('ESTCD_ID', db.Integer, primary_key=True)
    id_empresa = db.Column('EMPR_CODEMP', db.Integer)
    id_produto = db.Column('ITEM_COD_ITEM_LOG', db.String(20))
    qtdade     = db.Column('QTD', db.Numeric(17, 4))

class WmsPredio(db.Model):
    __bind_key__  = 'wms'
    __tablename__ = 'WMS_PREDIOS'
    id_predio  = db.Column('PREDIO_ID', db.Integer, primary_key=True)
    cod_predio = db.Column('COD_PREDIO', db.String(4))
    id_rua     = db.Column('RUASARM_COD_RUASARM', db.String(5))
    id_regiao  = db.Column('REGIAO_SEPARACAO', db.ForeignKey('WMS_REGIOES_SEPARACOES.COD_REGSEP'))

    regiao     = db.relationship('WmsRegiaoSeparacao', backref=db.backref('predio'))

class WmsSeparadoresTarefas(db.Model):
    __bind_key__  = 'wms'
    __tablename__ = 'STOKY_COLABORADOR_POR_TAREFA'
    id = db.Column('COD_TAREFA_CD', db.Integer, primary_key=True)
    idOnda = db.Column('ONDA_ONDA_ID', db.Integer)
    idProduto = db.Column('CODIGO', db.String(10))
    idColaborador = db.Column('COD_COLAB', db.Integer)
    nomeColaborador = db.Column('NOME', db.String(45), nullable=False)
    idTipoTarefa = db.Column('TAREFAS_COD_TAREFA', db.Integer)
    dataTarefa = db.Column('DTHR', db.Date())

class WmsTarefasCd(db.Model):
    __bind_key__ = 'wms'
    __tablename__ = 'WMS_TAREFAS_CD'
    id_centro_dist = db.Column('CENTDIST_COD_CENTDIST', db.Integer, primary_key=True)
    id_tarefa_cd = db.Column('COD_TAREFA_CD', db.Integer, primary_key=True)
    id_empresa = db.Column('EMPR_CODEMP', db.Integer, primary_key=True)
    id_tipo_tarefa = db.Column('TAREFAS_COD_TAREFA', db.String(6))
    id_predio_origem = db.Column('LA_PREDIO_PREDIO_ID_ORIGEM', db.ForeignKey('WMS_PREDIOS.PREDIO_ID'))
    liberada = db.Column('LIBERADA', db.String(1), db.CheckConstraint("liberada == 'S' or liberada == 'N'"))
    data_tarefa = db.Column('DTHR', db.Date())

    predio = db.relationship('WmsPredio', backref=db.backref('tarefas'))
