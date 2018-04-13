from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('oracle://fullwms:fullwms@192.168.104.4', echo=False)
Base = declarative_base(engine)


class Erros(Base):
    """"""
    __tablename__ = 'STOKY_COLABORADOR_POR_TAREFA'
    __table_args__ = {'autoload': True}

    id = Column('COD_TAREFA_CD', Integer, primary_key=True)
    onda = Column('ONDA_ONDA_ID', Integer, primary_key=True)
    # produto = Column('CODIGO', String(10))


def loadSession():
    """"""
    metadata = Base.metadata
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def getOnda():
    se = loadSession()

    obj = se.query(Erros)
    obj = obj.filter(Erros.onda == 48133)
    obj = obj.filter(Erros.codigo == '33199')
    # obj = obj.all()
    print(obj.count())
    for o in obj:
        print(o.codigo, o.nome)


if __name__ == '__main__':
    getOnda()
