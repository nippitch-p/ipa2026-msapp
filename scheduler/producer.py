import os
import pika


def produce(body):
    host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    port = int(os.environ.get("RABBITMQ_PORT", "5672"))
    username = os.environ.get("RABBITMQ_DEFAULT_USER", "admin")
    password = os.environ.get("RABBITMQ_DEFAULT_PASS", "rabbitmq")
    queue = os.environ.get("RABBITMQ_QUEUE", "router_jobs")

    credentials = pika.PlainCredentials(
        username,
        password
    )

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=credentials
        )
    )

    channel = connection.channel()

    channel.exchange_declare(
        exchange="jobs",
        exchange_type="direct",
        durable=True
    )

    channel.queue_declare(
        queue=queue,
        durable=True
    )

    channel.queue_bind(
        queue=queue,
        exchange="jobs",
        routing_key="check_interfaces"
    )

    channel.basic_publish(
        exchange="jobs",
        routing_key="check_interfaces",
        body=body,
        properties=pika.BasicProperties(
            delivery_mode=2
        )
    )

    print(f"Message published to {queue}")

    connection.close()


if __name__ == "__main__":
    produce(b"192.168.1.44")
