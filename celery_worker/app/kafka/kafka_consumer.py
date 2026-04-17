import json
import logging

from confluent_kafka import Consumer, KafkaError

from app.tasks import calculate_order_prices

logger = logging.getLogger(__name__)
from app.celery_app import app



class KafkaOrderConsumer:
    def __init__(self):
        self.config = {
            'bootstrap.servers': 'kafka:29092',
            'group.id': 'celery_worker',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False,
        }
        self.consumer = Consumer(self.config)
        self.topic = 'ORDER_CREATED'
        self._ensure_celery_connection()

    def _ensure_celery_connection(self):
        try:
            with app.connection() as conn:
                conn.ensure_connection(max_retries=3, interval_start=1, interval_step=1, interval_max=3)
        except Exception as e:
            logger.error(f"Failed to pre-connect to Celery broker: {e}")
            raise

    def process_message(self, msg):
        try:
            payload = json.loads(msg.value().decode('utf-8'))
        except json.decoder.JSONDecodeError as e:
            logger.warning(f"Message decode error: {e}")
            self.consumer.commit(message=msg)
            return

        try:
            calculate_order_prices.delay(payload)
            self.consumer.commit(message=msg)
        except Exception as e:
            logger.error(f"Failed to send task to Celery: {e}")

    def consume(self):
        self.consumer.subscribe([self.topic])
        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        logger.error(f"Kafka error: {msg.error()}")
                    continue

                self.process_message(msg)

        finally:
            self.consumer.close()


if __name__ == '__main__':
    consumer = KafkaOrderConsumer()
    consumer.consume()
