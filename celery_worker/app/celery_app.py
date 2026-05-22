from celery import Celery
from celery.schedules import crontab
from prometheus_client import start_http_server

from app.config import settings
from app.logging.logging_config import setup_json_logging

app = Celery('celery_worker', broker=f'redis://{settings.redis_host}:{settings.redis_port}/1', include=['app.tasks'])

app.conf.update(timezone='UTC',
                enable_utc=True,
                beat_schedule={
                    "update_currency_rate": {
                        "task": "update_currency_rate",
                        "schedule": crontab(minute=0),
                    }
                },
                worker_hijack_root_logger=False
                )

setup_json_logging()
start_http_server(8004, '0.0.0.0')
