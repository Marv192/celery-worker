from prometheus_client import start_http_server

from app.kafka.kafka_consumer import KafkaOrderConsumer

start_http_server(8003, '0.0.0.0')
consumer = KafkaOrderConsumer()
consumer.consume()
