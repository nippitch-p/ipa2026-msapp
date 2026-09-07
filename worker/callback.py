from bson import json_util

from router_client import get_interfaces
from database import save_interface_status


def callback(ch, method, properties, body):

    job = json_util.loads(body.decode())

    router_ip = job["ip"]
    router_username = job["username"]
    router_password = job["password"]

    print(f"Received job for router {router_ip}")

    try:

        interfaces = get_interfaces(
            router_ip,
            router_username,
            router_password
        )

        print("Interfaces:")
        print(interfaces)

        save_interface_status(
            router_ip,
            interfaces
        )

        print(
            f"Saved interface status "
            f"for {router_ip}"
        )

        ch.basic_ack(
            delivery_tag=method.delivery_tag
        )

    except Exception as e:

        print(f"Error: {e}")

        ch.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=True
        )
