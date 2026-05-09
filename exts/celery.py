import platform
from celery import Celery
from config import Config

celery = Celery(__name__, broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)

# Windows 下 Celery 不支持 prefork，必须用 solo；Linux/Docker 下用默认的 prefork
if platform.system() == 'Windows':
    celery.conf.update(
        worker_pool='solo',
        worker_concurrency=1,
    )

# 配置 Celery 与 Flask 应用集成
def make_celery(app):
    celery1 = celery
    celery1.conf.update(app.config)

    class ContextTask(celery1.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery1.Task = ContextTask
    return celery1

# 使用方法
# Windows 本地开发:
#   终端1: redis-server
#   终端2: celery -A app:celery worker --loglevel=info --pool=solo
#   终端3: python app.py
#
# Docker 生产部署:
#   docker compose up -d --build  （Celery worker 作为独立容器自动启动）