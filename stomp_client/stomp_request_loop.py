# Sends 3 different operations based on user input to topic beergarden/operations, and request in the header for a
# response to be sent to topic replyto
import json
import signal
import stomp
import time
from brewtils.models import Operation, Request, System
from brewtils.schema_parser import SchemaParser

conn = None


def keyboardInterruptHandler(signal, frame):
    global conn
    if conn.is_connected():
        conn.disconnect()
    exit(0)


def send():
    global conn
    count = 0
    operation = None
    host_and_ports = [('localhost', 61613)]
    conn = stomp.Connection(host_and_ports=host_and_ports, heartbeats=(10000, 0))
    try:
        conn.connect('beer_garden', 'password', wait=True, headers={'client-id': 'beer_garden'})
    except:
        pass

    signal.signal(signal.SIGINT, keyboardInterruptHandler)
    # Sending a Request
    request_model = Request(system="echo-sleeper",
                            system_version="1.0.0.dev0",
                            instance_name="default",
                            command="say_sleep",
                            parameters={'message': 'Hello, World!', 'loud': False, 'amount': 10},
                            namespace='default',
                            metadata={'reply-to': 'metadataReplyto'}, )

    wait_timeout = 0
    sample_operation_request = Operation(operation_type="REQUEST_CREATE",
                                         model=request_model,
                                         model_type="Request",
                                         kwargs={"wait_timeout": wait_timeout},
                                         )

    operation = sample_operation_request
    while True:
        count = count + 1
        count_str = "request count: " + count.__str__()
        operation.model.parameters['message'] = count_str
        while not conn.is_connected():
            try:
                conn.connect('beer_garden', 'password', wait=True, headers={'client-id': 'beer_garden'})
            except:
                pass
        conn.send(body=SchemaParser.serialize_operation(operation, to_string=True),
                  headers={'reply-to': 'replyto', 'model_class': operation.__class__.__name__},
                  destination='Beer_Garden_Events_test')
        with open("count.json", "w") as outfile:
            json.dump(count.__str__(), outfile)
        time.sleep(.01)


send()
if conn.is_connected():
    conn.disconnect()
