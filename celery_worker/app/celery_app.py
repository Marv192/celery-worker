from celery import Celery
from celery.schedules import crontab

from app.config import settings

app = Celery('celery_worker', broker=f'redis://{settings.redis_host}:{settings.redis_port}/1', include=['app.tasks'])

app.conf.update(timezone='UTC',
                enable_utc=True,
                beat_schedule={
                    "update_currency_rate": {
                        "task": "update_currency_rate",
                        "schedule": crontab(minute=0),
                    }
                }
                )
