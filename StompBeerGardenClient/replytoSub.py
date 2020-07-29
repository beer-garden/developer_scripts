# Subscribes to replyto topic to get responses requested from an actor if reply-to was specified as replyto in the
# header. Also the queue made from the subscription is durable so after disconnection the queue is not removed so it
# can get missed messages after reconnection. The message will be forwarded to metadataReplyto if the event payload
# has attribute metadata with a key 'reply-to' and a value of metadataReplyto

import signal
import stomp
from brewtils.models import Operation, Request, System, Events, Event
from brewtils.schema_parser import SchemaParser

conn = None


def keyboardInterruptHandler(signal, frame):
    global conn
    if conn.is_connected():
        conn.disconnect()
    exit(0)


class MessageListener(object):
    def on_error(self, headers, message):
        print('received an error %s' % headers)

    def on_message(self, headers, message):
        print("Raw message:", message)
        try:
            parsed = SchemaParser.parse(message, from_string=True, model_class=eval(headers['model_class']),
                                        many="True" == headers["many"])
            print("Parsed message:", parsed)
        except AttributeError:
            print("AttributeError: unable to parse message.")


def listen():
    global conn
    conn = stomp.Connection(host_and_ports=[('localhost', 61613)], heartbeats=(10000, 0))
    conn.set_listener('', MessageListener())
    conn.connect('beer_garden', 'password', wait=True, headers={'client-id': 'ReplyTo'})
    conn.subscribe(destination='replyto', id="replyto_listener", ack='auto',
                   headers={'subscription-type': 'MULTICAST', 'durable-subscription-name': 'replyto'})

    signal.signal(signal.SIGINT, keyboardInterruptHandler)
    while True:
        pass


listen()
