import os
import time
import pika

from dotenv import load_dotenv
from callback import callback

load_dotenv()

user = os.getenv("RABBITMQ_DEFAULT_USER")
pwd = os.getenv("RABBITMQ_DEFAULT_PASS")
host = os.getenv("RABBITMQ_HOST", "localhost")
port = int(os.getenv("RABBITMQ_PORT", "5672"))
queue = os.getenv("RABBITMQ_QUEUE", "router_jobs")


def consume():
    for attempt in range(10):
        try:
            print(f"Connecting to RabbitMQ at {host}:{port} (try {attempt})...")

            creds = pika.PlainCredentials(user, pwd)

            conn = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=host,
                    port=port,
                    credentials=creds
                )
            )

            print("Connected to RabbitMQ")
            break

        except Exception as e:
            print(f"Failed: {e}")
            time.sleep(5)

    else:
        print("Could not connect after 10 attempts")
        exit(1)

    ch = conn.channel()

    ch.queue_declare(
        queue=queue,
        durable=True
    )

    ch.basic_qos(prefetch_count=1)

    ch.basic_consume(
        queue=queue,
        on_message_callback=callback,
        auto_ack=False
    )

    print(f"Waiting for messages on {queue}...")

    ch.start_consuming()


if __name__ == '__main__':
    consume()
