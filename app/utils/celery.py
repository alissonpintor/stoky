from celery import Celery


class Task():
    celery = None
    
    def __setattr__(self, name, value):
        raise Exception('Task e um classe estatica')
    
    @classmethod
    def get_celery(cls):
        return cls.celery
    
    @classmethod
    def set_celery(cls, app):
        cls.celery = Celery(
            app.name,
            backend=app.config['CELERY_BROKER_URL'],
            broker=app.config['CELERY_BROKER_URL'])
        cls.celery.conf.update(app.config)

        TaskBase = cls.celery.Task
        class ContextTask(TaskBase):
            abstract = True
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return TaskBase.__call__(self, *args, **kwargs)
        cls.celery.Task = ContextTask