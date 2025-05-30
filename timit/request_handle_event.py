from brewtils.models import Request, Event
from beer_garden.db.mongo.api import check_connection, create_connection
from beer_garden import config
from beer_garden.requests import handle_event
from bson.objectid import ObjectId

import datetime
import sys
import random
import timeit
import functools

db_config = {
    "connection": {
        "host": "localhost",
        "port": 27017,
        "username": None,
        "password": None,
    },
    "name": "beer_garden",
}

config._CONFIG = {"garden":{"name":"test"}, "db": {"prune": {"batch_size": -1, "ttl": {"info": 1, "action": 1}}}}

# Make connection to mongo and verify it works
create_connection(db_config = db_config)
check_connection(db_config)

size = 100
parameters = {"input": "".join(("a" for _ in range (size - sys.getsizeof(""))))}
output="".join(("a" for _ in range (size - sys.getsizeof(""))))

created_total = 0
in_progress_total = 0
success_total = 0

def generate_request_history(created_total, in_progress_total, success_total):
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
    create_time_taken = timeit.timeit(functools.partial(handle_event, event), number=1)
    if created_total:
        created_total = created_total + create_time_taken
    else:
        created_total = create_time_taken

    request.status="IN_PROGRESS"
    request.updated_at = datetime.datetime.now()
    in_progress_time_taken = timeit.timeit(functools.partial(handle_event, event), number=1)

    if in_progress_total:
        in_progress_total = in_progress_total + in_progress_time_taken
    else:
        in_progress_total = in_progress_time_taken


    request.status="SUCCESS"
    request.output = output
    request.updated_at = datetime.datetime.now()
    success_time_taken = timeit.timeit(functools.partial(handle_event, event), number=1)
    if success_total:
        success_total = success_total + success_time_taken
    else:
        success_total = success_time_taken

    return created_total, in_progress_total, success_total

test_total = 1000
for _ in range(test_total):
    created_total, in_progress_total, success_total = generate_request_history(created_total, in_progress_total, success_total)

print(f"Create event: {(created_total/test_total):.6f} seconds")
print(f"In Progress event: {(in_progress_total/test_total):.6f} seconds")
print(f"Success event: {(success_total/test_total):.6f} seconds")