import json
import logging

from confluent_kafka import Consumer, KafkaError
from pydantic import ValidationError

from app.schemas.order_message import OrderMessageReceived
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
            logger.exception("Failed to pre-connect to Celery broker", extra={"error_type": type(e).__name__})
            raise

    def process_message(self, msg):
        try:
            raw_payload = json.loads(msg.value().decode('utf-8'))
            raw_headers = msg.headers() or []
            headers = {k: v.decode('utf-8') for k, v in raw_headers}
            order_payload = raw_payload.get("data") if "data" in raw_payload else raw_payload

            order_data = OrderMessageReceived.model_validate(order_payload)

        except json.decoder.JSONDecodeError:
            logger.warning("Message decode error", extra={
                "topic": msg.topic(),
                "partition": msg.partition(),
                "offset": msg.offset()
            })
            self.consumer.commit(message=msg)
            return

        except ValidationError as e:
            logger.error("Message validation error", extra={
                "error_type": type(e).__name__,
                "errors": [err["msg"] for err in e.errors()],
                "order_payload": order_payload,
            })
            self.consumer.commit(message=msg)
            return

        except Exception as e:
            logger.exception("Decoding or validation error", extra={"error_type": type(e).__name__})
            self.consumer.commit(message=msg)
            return

        try:
            celery_payload = {**order_data.model_dump(mode='json'), "headers": headers}
            calculate_order_prices.delay(celery_payload)
            self.consumer.commit(message=msg)
            logger.info("Message processed", extra={"order_id": str(order_data.order_id)})
        except Exception as e:
            logger.exception("Failed to send task to Celery", extra={"error_type": type(e).__name__})

    def consume(self):
        self.consumer.subscribe([self.topic])
        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        logger.warning(f"Kafka error: {msg.error()}")
                    continue

                self.process_message(msg)

        finally:
            self.consumer.close()
