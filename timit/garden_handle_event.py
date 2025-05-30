from brewtils.models import Request, Event, System, Garden
from beer_garden.db.mongo.api import check_connection, create_connection
from beer_garden import config
from beer_garden.garden import handle_event
from bson.objectid import ObjectId
from beer_garden.systems import create_system
from beer_garden.events.processors import FanoutProcessor
import copy
from beer_garden.db.mongo import models
import datetime
import sys
import random
import timeit
import functools
import beer_garden


beer_garden.events.manager = FanoutProcessor(name="event manager")

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

create_connection(db_config = db_config)
check_connection(db_config)

# Clear the database
def clean_database(add_systems = 0):
    models.Garden.drop_collection()
    models.System.drop_collection()
    models.Topic.drop_collection()

    # Load 20 local systems into the database
    garden = models.Garden(connection_type="LOCAL")
    garden.name = config.get("garden.name")
    garden.version = "3.30.0"
    garden.save()

    if add_systems > 0:
        for index in range(add_systems):
            system = System(name=f"system_{index}", version="1.2.3", namespace=config.get("garden.name"), local=True)
            create_system(system)

def build_event(add_local_systems = 0, add_remote_systems = 0):

    remote_systems = []
    # 10 actual remote systems
    if add_remote_systems > 0:
        for index in range(add_remote_systems):
            system = System(id=str(ObjectId()), name=f"remote_system_{index}", version="1.2.3", namespace="remote", local=True)
            remote_systems.append(system)

    # 5 Overlap
    if add_local_systems > 0:
        for index in range(add_local_systems):
            system = System(id=str(ObjectId()), name=f"system_{index}", version="1.2.3", namespace=config.get("garden.name"), local=True)
            remote_systems.append(system)

    # Remote Garden
    remote_garden = Garden(id=str(ObjectId()), connection_type="REMOTE", name="remote", systems=remote_systems, children=[])


    event = Event(
            name="GARDEN_SYNC",
            payload=remote_garden,
            payload_type="Garden",
            garden=remote_garden.name,
        )
    
    return event


def run_handler(event):
    copy_event = copy.deepcopy(event)
    start = timeit.default_timer()
    handle_event(copy_event)
    stop = timeit.default_timer()

    return stop - start

def run_test(local_garden_systems, remote_garden_systems, overlap_systems, results_file):
    event = build_event(overlap_systems, remote_garden_systems)

    # First run
    total_loops = 1000
    initial_time_taken = 0
    for _ in range(total_loops):
        clean_database(local_garden_systems)
        initial_time_taken = initial_time_taken + run_handler(event)


    sync_time_taken = 0
    total_systems = len(event.payload.systems)
    current_system_pop = 0

    # total_loops = 1000
    for _ in range(total_loops):
        copy_event = copy.deepcopy(event)
        if current_system_pop >= total_systems:
            current_system_pop = 0

        copy_event.payload.systems.pop(current_system_pop)
        sync_time_taken = sync_time_taken + run_handler(copy_event)

        current_system_pop = current_system_pop + 1

    print(f"{local_garden_systems}/{remote_garden_systems}/{overlap_systems}")
    print(f"First event: {(initial_time_taken/total_loops):.6f} seconds")
    print(f"Sync event: {(sync_time_taken/total_loops):.6f} seconds")

    results_file.write(f"{local_garden_systems}/{remote_garden_systems}/{overlap_systems}\n")
    results_file.write(f"First event: {(initial_time_taken/total_loops):.6f} seconds\n")
    results_file.write(f"Sync event: {(sync_time_taken/total_loops):.6f} seconds\n")

    return initial_time_taken, sync_time_taken

with open("results.txt", "w") as results_file:
    results_file.write("Total Local Systems, Total Remote Systems, Total Overlap Systems\n")
    
    first, second = run_test(10,10,1, results_file)
    first, second = run_test(10,20,1, results_file)
    first, second = run_test(10,30,1, results_file)
    first, second = run_test(10,40,1, results_file)
    first, second = run_test(10,50,1, results_file)
    first, second = run_test(10,60,1, results_file)
    first, second = run_test(10,70,1, results_file)

    # first, second = run_test(0,10,0, results_file)
    # first, second = run_test(0,20,0, results_file)
    # first, second = run_test(0,30,0, results_file)
    # first, second = run_test(0,40,0, results_file)
    # first, second = run_test(0,50,0, results_file)
    # first, second = run_test(0,60,0, results_file)
    # first, second = run_test(0,70,0, results_file)
