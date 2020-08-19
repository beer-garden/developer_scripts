# Sends 3 different operations based on user input to topic beergarden/operations, and request in the header for a
# response to be sent to topic replyto


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


def sendHeartbeat():
    global conn
    while conn.is_connected:
        time.sleep(30)
        conn.send(body="heartbeat", destination='heartbeat')


def send():
    global conn
    operation = None
    conn = stomp.Connection(host_and_ports=[('localhost', 61613)], heartbeats=(10000, 0))
    conn.connect('beer_garden', 'password', wait=True, headers={'client-id': 'SendMessage'})

    signal.signal(signal.SIGINT, keyboardInterruptHandler)
    # Sending a Request
    request_model = Request(system="echo",
                            system_version="1.0.0.dev0",
                            instance_name="default",
                            command="say",
                            parameters={'message': 'Hello, World!', 'loud': True},
                            namespace='default',
                            metadata={'reply-to': 'metadataReplyto'}, )

    wait_timeout = 0
    sample_operation_request = Operation(operation_type="REQUEST_CREATE",
                                         model=request_model,
                                         model_type="Request",
                                         kwargs={"wait_timeout": wait_timeout},
                                         )

    # Request all Systems
    sample_operation_systems = Operation(
        operation_type="SYSTEM_READ_ALL"
    )

    sample_operation_read = Operation(
        operation_type="REQUEST_READ",
        args={"5f295ceb82f2dbf9740ba41e"},
    )
    operations = {'1': sample_operation_request, '2': sample_operation_read, '3': sample_operation_systems, '4': 'quit'}
    while operation is not "quit":
        in_put = input("1: sample_operation_request, 2: sample_operation_read, "
                       "3: sample_operation_systems, 4: 'quit'\n Enter corresponding number: ")
        if in_put in operations:
            if in_put is "2":
                operations[in_put].args = {input("Enter request id: ")}
            operation = operations[in_put]
            if operation is not "quit":
                conn.send(body=SchemaParser.serialize_operation(operation, to_string=True),
                          headers={'reply-to': 'replyto'}, destination='beergarden/operations')
        else:
            print("Error: Input is not valid")

    if conn.is_connected():
        conn.disconnect()


send()
