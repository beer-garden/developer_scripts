#!/usr/bin/env python

"""
Subscribes to replyto topic to get responses requested from an actor if reply-to was specified as replyto in the
header. Also the queue made from the subscription is durable so after disconnection the queue is not removed so it
can get missed messages after reconnection. The message will be forwarded to metadataReplyto if the event payload
has attribute metadata with a key 'reply-to' and a value of metadataReplyto
"""

import signal

import brewtils.models
import stomp
from brewtils.schema_parser import SchemaParser

conn: stomp.Connection


def signal_handler(_, __):
    if conn.is_connected():
        conn.disconnect()


class MessageListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print(f"Received an error:\n\tMessage: {message}\n\tHeaders: {headers}")

    def on_message(self, headers, message):
        try:
            parsed = SchemaParser.parse(
                message,
                getattr(brewtils.models, headers["model_class"]),
                from_string=True,
                many="True" == headers["many"],
            )

            print(f"Parsed message: {parsed!r}")
        except AttributeError:
            print("AttributeError: unable to parse message.")


def listen():
    global conn
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

    conn.set_listener("", MessageListener())

    conn.subscribe(
        destination="replyto",
        id="replyto_listener",
        ack="auto",
        headers={
            "subscription-type": "MULTICAST",
            "durable-subscription-name": "replyto",
        },
    )

    print("All set, just waiting for messages!")

    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()


if __name__ == "__main__":
    listen()
