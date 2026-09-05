import os
import json
import pika
import textfsm

from pymongo import MongoClient
from datetime import datetime, timezone

from netmiko import ConnectHandler


# ========================================
# MongoDB
# ========================================

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb://admin:mongo@mongo:27017/?authSource=admin"
)

DB_NAME = os.environ.get(
    "DB_NAME",
    "ipa2026"
)

mongo_client = MongoClient(MONGO_URI)

db = mongo_client[DB_NAME]

router_results = db["router_results"]


# ========================================
# TextFSM
# ========================================

TEMPLATE_FILE = (
    "/app/templates/"
    "cisco_ios_show_ip_interface_brief.textfsm"
)


def parse_interface(output):

    with open(TEMPLATE_FILE) as template_file:

        template = textfsm.TextFSM(template_file)

        records = template.ParseText(output)


    interfaces = []

    for record in records:

        interfaces.append({
            "interface": record[0],
            "ip_address": record[1],
            "ok": record[2],
            "method": record[3],
            "status": record[4].strip(),
            "protocol": record[5]
        })

    return interfaces


# ========================================
# Connect Router
# ========================================

def check_router(router):

    ip = router["ip"]
    username = router["username"]
    password = router["password"]


    device = {
        "device_type": "cisco_ios",
        "host": ip,
        "username": username,
        "password": password
    }


    print(f"Connecting to router {ip}")


    connection = ConnectHandler(**device)


    try:

        output = connection.send_command(
            "show ip interface brief"
        )

        print("RAW OUTPUT:")
        print(output)


        # ========================================
        # Parse ด้วย TextFSM
        # ========================================

        interfaces = parse_interface(output)


        print("PARSED INTERFACES:")
        print(interfaces)


        # ========================================
        # Save MongoDB
        # ========================================

        document = {
            "router_ip": ip,
            "command": "show ip interface brief",
            "interfaces": interfaces,
            "timestamp": datetime.now(timezone.utc)
        }


        router_results.insert_one(document)


        print("Saved result to MongoDB")


    finally:

        connection.disconnect()


# ========================================
# RabbitMQ Callback
# ========================================

def callback(ch, method, properties, body):

    print("================================")
    print("Message received")
    print(body)


    try:

        router = json.loads(body)

        check_router(router)


        # บอก RabbitMQ ว่าทำงานสำเร็จ
        ch.basic_ack(
            delivery_tag=method.delivery_tag
        )


    except Exception as e:

        print("ERROR:", e)

        # ถ้าต้องการให้ message กลับเข้า Queue
        ch.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=True
        )


# ========================================
# RabbitMQ
# ========================================

def worker():

    host = os.environ.get(
        "RABBITMQ_HOST",
        "rabbitmq"
    )

    port = int(
        os.environ.get(
            "RABBITMQ_PORT",
            "5672"
        )
    )

    username = os.environ.get(
        "RABBITMQ_DEFAULT_USER",
        "admin"
    )

    password = os.environ.get(
        "RABBITMQ_DEFAULT_PASS",
        "rabbitmq"
    )

    queue = os.environ.get(
        "RABBITMQ_QUEUE",
        "router_jobs"
    )


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


    channel.queue_declare(
        queue=queue,
        durable=True
    )


    channel.basic_qos(
        prefetch_count=1
    )


    channel.basic_consume(
        queue=queue,
        on_message_callback=callback
    )


    print(
        f"Worker1 waiting for messages "
        f"on queue: {queue}"
    )


    channel.start_consuming()


# ========================================
# Main
# ========================================

if __name__ == "__main__":

    worker()
