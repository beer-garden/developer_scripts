#!/usr/bin/env python

"""
Subscribes to metadataReplyto topic to get messages sent from eventSub if the event
payload has attribute metadata with a key 'reply-to' and a value of metadataReplyto.
Also the queue made from the subscription is durable so after disconnection the queue
is not removed so it can get missed messages after reconnection.
"""

import signal

import stomp
from brewtils.schema_parser import SchemaParser

conn: stomp.Connection


def signal_handler(_, __):
    global conn
    if conn.is_connected():
        conn.disconnect()


class MessageListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print("received an error %s" % headers)

    def on_message(self, headers, message):
        print("Raw message:", message)
        try:
            parsed = SchemaParser.parse(
                message,
                from_string=True,
                model_class=eval(headers["model_class"]),
                many="True" == headers["many"],
            )
            print("Parsed message:", parsed)
        except AttributeError:
            print("AttributeError: unable to parse message.")


def listen():
    global conn
    key = "./certs/server_key.pem"
    cert = "./certs/server_certificate.pem"
    host_and_ports = [("localhost", 61613)]
    conn = stomp.Connection(host_and_ports=host_and_ports, heartbeats=(10000, 0))
    try:
        conn.connect(
            "beer_garden", "password", wait=True, headers={"client-id": "beer_garden"}
        )
    except:
        conn = stomp.Connection(host_and_ports=host_and_ports, heartbeats=(10000, 0))
        conn.set_ssl(for_hosts=host_and_ports, key_file=key, cert_file=cert)
        conn.connect(
            "beer_garden", "password", wait=True, headers={"client-id": "beer_garden"}
        )
    conn.set_listener("", MessageListener())
    conn.subscribe(
        destination="metadataReplyto",
        id="MetadataListener",
        ack="auto",
        headers={
            "subscription-type": "MULTICAST",
            "durable-subscription-name": "metadataReplyto",
        },
    )

    print("All set, just waiting for messages!")

    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()


if __name__ == "__main__":
    listen()
