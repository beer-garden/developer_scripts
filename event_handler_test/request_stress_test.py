import calendar
import datetime
from concurrent.futures import ThreadPoolExecutor, wait

import bson
import requests
import time
import random
hostname = "localhost"
url = f"http://{hostname}:2337/api/v1/forward"
garden = "default"
child_garden = "child"
my_list = [0.1, 0.2, 0.3, 0.4, 0.5]

def current_time():
    localized = datetime.datetime.now(datetime.timezone.utc)
    return (calendar.timegm(localized.timetuple()) * 1000) + int(
        localized.microsecond / 1000
    )


def post_event(event):
    requests.post(url, json=event, headers={"Content-Type": "application/json"})


def create_request_events(request_id, loop):

    time.sleep( random.choice(my_list))
    create_time = current_time()
    event = {
        "name": "REQUEST_CREATED",
        "garden": child_garden,
        "payload_type": "Request",
        "payload": {
            "id": request_id,
            "system": "echo",
            "is_event": False,
            "updated_at": create_time,
            "metadata": {},
            "has_parent": False,
            "command_type": "ACTION",
            "children": [],
            "created_at": create_time,
            "instance_name": "default",
            "source_garden": "default",
            "system_version": "3.0.0.dev0",
            "output": "Hello, World!",
            "parameters": {"message": "Hello, World!", "loud": False},
            "target_garden": garden,
            "requester": "anonymous",
            "hidden": False,
            "command": "say",
            "status": "CREATED",
            "status_updated_at": create_time,
            "comment": f"Forward Operation Stress Loop {loop} -- {current_time()}",
            "namespace": garden,
        },
    }

    operation = {
        "operation_type": "PUBLISH_EVENT",
        "model": event,
        "model_type": "Event",
        "source_garden_name": child_garden,
    }

    post_event(operation)

    event["name"] = "REQUEST_UPDATED"
    event["payload"]["status"] = "IN_PROGRESS"
    event["payload"]["status_updated_at"] = current_time()

    time.sleep( random.choice(my_list))
    post_event(operation)

    event["name"] = "REQUEST_COMPLETED"
    event["payload"]["status"] = "SUCCESS"
    event["payload"]["status_updated_at"] = current_time()

    time.sleep( random.choice(my_list))
    post_event(operation)


def generate_random_mongo_id():
    return str(bson.ObjectId())

import time

print("Starting Event Generator")
for loop in range(3000):
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=50) as executor:
        
            futures = [
                executor.submit(create_request_events, generate_random_mongo_id(), loop,)
                for _ in range(1000)
            ]
            wait(futures)
    end_time = time.time()
    elapsed_time = end_time - start_time
    rate = round((1000 * 3) / (elapsed_time / 60), 2)
    requests_rate = round(1000/ (elapsed_time / 60), 2)
    print(f"Publishing {rate} Events and {requests_rate} Requests per minute")