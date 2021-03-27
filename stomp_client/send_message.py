#!/usr/bin/env python

"""
Sends 3 different operations based on user input to topic beergarden/operations, and
request in the header for a response to be sent to topic replyto
"""


import signal
import time

import stomp
from brewtils.models import Operation, Request
from brewtils.schema_parser import SchemaParser

conn: stomp.Connection


def signal_handler(_, __):
    if conn.is_connected():
        conn.disconnect()


def sendHeartbeat():
    while conn.is_connected:
        time.sleep(30)
        conn.send(body="heartbeat", destination="heartbeat")


def send():
    global conn
    operation = None
    host_and_ports = [("localhost", 61613)]
    conn = stomp.Connection(host_and_ports=host_and_ports, heartbeats=(10000, 0))

    try:
        conn.connect(
            "beer_garden", "password", wait=True, headers={"client-id": "beer_garden"}
        )
    except:
        print("Connection attempt failed, attempting TLS connection")

        key = "./certs/server_key.pem"
        cert = "./certs/server_certificate.pem"
        conn.set_ssl(for_hosts=host_and_ports, key_file=key, cert_file=cert)

        conn.connect(
            "beer_garden", "password", wait=True, headers={"client-id": "beer_garden"}
        )

    signal.signal(signal.SIGINT, signal_handler)

    # Sending a Request
    request_model = Request(
        system="echo",
        system_version="1.0.0.dev0",
        instance_name="default",
        command="say",
        parameters={"message": "Hello, World!", "loud": True},
        namespace="default",
        metadata={"reply-to": "metadataReplyto"},
    )

    wait_timeout = 0
    sample_operation_request = Operation(
        operation_type="REQUEST_CREATE",
        model=request_model,
        model_type="Request",
        kwargs={"wait_timeout": wait_timeout},
    )

    # Request all Systems
    sample_operation_systems = Operation(operation_type="SYSTEM_READ_ALL")

    sample_operation_read = Operation(
        operation_type="REQUEST_READ",
        args={"5f295ceb82f2dbf9740ba41e"},
    )
    operations = {
        "1": sample_operation_request,
        "2": sample_operation_read,
        "3": sample_operation_systems,
        "4": "quit",
    }
    while operation != "quit":
        in_put = input(
            "1: sample_operation_request, 2: sample_operation_read, "
            "3: sample_operation_systems, 4: 'quit'\n Enter corresponding number: "
        )
        if in_put in operations:
            if in_put == "2":
                operations[in_put].args = {input("Enter request id: ")}
            operation = operations[in_put]

            if operation != "quit":
                conn.send(
                    body=SchemaParser.serialize_operation(operation, to_string=True),
                    headers={
                        "reply-to": "replyto",
                        "model_class": operation.__class__.__name__,
                    },
                    destination="Beer_Garden_Operations",
                )
        else:
            print("Error: Input is not valid")

    if conn.is_connected():
        conn.disconnect()


if __name__ == "__main__":
    send()
