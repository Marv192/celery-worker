from celery import Celery
from celery.schedules import crontab

from app.utils.redis import REDIS_URL

app = Celery('celery_worker', broker=f'{REDIS_URL}/1', include=['app.tasks'])

app.conf.update(timezone='UTC',
                enable_utc=True,
                beat_schedule={
                    "update_currency_rate": {
                        "task": "app.tasks.update_currency_rate",
                        "schedule": crontab(minute=0),
                    }
                }
                )
