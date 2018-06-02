from flask_sqlalchemy import Model
from sqlalchemy import exc as core_exc
from sqlalchemy.orm import exc

class Result(object):
    """
        Classe que recebe o resultado
    """
    def __init__(self, status, message):
        self.status = status
        self.message = message


class BaseModel(Model):
    """
        classe Model base que contem metodos comuns
        como delete, search by id, update
    """
    def update(self):
        from app import db
        
        try:
            db.session.add(self)
            db.session.commit()
            return Result(status=True, message='Registro realizado com sucesso')
        
        except Exception as e:
            return Result(status=False, message=str(e))
    
    def delete(self):
        from app import db
        
        try:
            db.session.delete(self)
            db.session.commit()
            return Result(status=True, message='Registro excluído com sucesso')
        
        except core_exc.IntegrityError:
            return Result(status=False, message='Não foi possível excluir. Erro de Integridade')
        
        except Exception as e:
            return Result(status=False, message=str(e))
    
    @classmethod
    def by_id(cls, id):
        from app import db

        primary_key = db.inspect(cls).primary_key[0]
        data = db.session.query(
            cls
        ).filter(
            primary_key==id
        ).first()
        
        return data
    
    @classmethod
    def by(cls, **kwargs):
        from app import db

        data = db.session.query(cls)

        for k, v in kwargs.items():
            if k.upper() in cls.__table__.columns.keys():
                column = cls.__table__.columns[k.upper()]
                data = data.filter(column==v)
        data = data.first()
        
        return data
    
    @classmethod
    def all(cls):
        from app import db

        data = cls.query.all()        
        return data