from brewtils.models import Request, Event
from bson.objectid import ObjectId
from brewtils import EasyClient
from concurrent.futures import ThreadPoolExecutor, as_completed

import datetime
import random
import sys
import timeit


# Sets max size to 4MB
max_total_size = 4 * 1_000_000

internal_loop = 100
external_loop = 1000

# slow_load = True
output_size = random.randint(1, max_total_size)
input_size = random.randint(1, max_total_size-output_size + 2)

size = 100
parameters = {"input": "".join(("a" for _ in range (size - sys.getsizeof(""))))}
output="".join(("a" for _ in range (size - sys.getsizeof(""))))

def generate_request_history():
    test_time = datetime.datetime.now()

    command_name = random.choice(["say","dont_say","echo","test"])
    system_name = random.choice(["echo_1","echo_2","test_1","test_2"])
    system_version = random.choice(["1.0.0","2.0.0","3.0.0","4.0.0"])
    instance_name = random.choice(["default","test","test_1","test_2"])
    command_type = random.choice(["ACTION","INFO"])

    request = Request(
        id=str(ObjectId()),
        namespace="generated",
        system=system_name,
        system_version=system_version,
        instance_name=instance_name,
        command=command_name,
        command_display_name=command_name,
        status="CREATED",
        command_type= command_type,
        comment=f"Created request",
        parameters=parameters,
        metadata={},
        updated_at = test_time,
        created_at = test_time
    )

    event = Event(
        name="REQUEST_UPDATED",
        payload=request,
        payload_type="Request",
        garden="Downstream-01-DEV",
    )

    easy_client = EasyClient(host="localhost", ssl_enabled=False)

    easy_client.publish_event(event)
    request.status="IN_PROGRESS"
    request.updated_at = datetime.datetime.now()
    easy_client.publish_event(event)

    request.status="SUCCESS"
    request.output = output
    request.updated_at = datetime.datetime.now()
    easy_client.publish_event(event)


def load_requests():
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures=[]
        for _ in range(internal_loop):
            futures.append(executor.submit(generate_request_history))

        for _ in as_completed(futures):
            pass

for i in range(external_loop):
    time_taken = timeit.timeit(load_requests, number=1)

    average_time = time_taken / internal_loop 

    print(f"Average time for loop: {average_time:.6f} seconds ({i + 1} of {external_loop})")
