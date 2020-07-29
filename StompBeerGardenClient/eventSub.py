# Subscribes to beergarden/events topic to get event messages. Also the queue made from the subscription is durable so
# after disconnection the queue is not removed so it can get missed messages after reconnection.

import signal
import stomp
from brewtils.models import Operation, Request, System, Event, Events
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
        global conn
        try:
            parsed = SchemaParser.parse(message, from_string=True, model_class=eval(headers['model_class']))
            print("Parsed message:", parsed)

            #  Forwards an event object to a destination if payload has a metadata
            try:
                if 'reply-to' in parsed.payload.metadata:
                    conn.send(body=message, headers=headers, destination=parsed.payload.metadata['reply-to'])
            except AttributeError:
                pass
        except AttributeError:
            print("Error: unable to parse message:", message)


def listen():
    global conn

    conn = stomp.Connection(host_and_ports=[('localhost', 61613)], heartbeats=(10000, 0))
    conn.set_listener('', MessageListener())
    conn.connect('beer_garden', 'password', wait=True, headers={'client-id': 'EventListener'})
    conn.subscribe(destination='beergarden/events', id='event_listener', ack='auto',
                   headers={'subscription-type': 'MULTICAST', 'durable-subscription-name': 'event'})
    signal.signal(signal.SIGINT, keyboardInterruptHandler)
    while True:
        pass


listen()
