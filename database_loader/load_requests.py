from beer_garden.db.mongo.models import Request
from beer_garden.db.mongo.api import check_connection, create_connection

import datetime
import random
import sys

# Set how many requests you want generated
target_requests = 1000

# Copy this info from your config.yaml file
db_config = {
    "connection": {
        "host": "localhost",
        "port": 27017,
        "username": None,
        "password": None,
    },
    "name": "beer_garden",
}

# Make connection to mongo and verify it works
create_connection(db_config = db_config)
check_connection(db_config)

# Give you something random in the last week
def random_date_last_week():
    today = datetime.date.today()
    last_week = today - datetime.timedelta(days=8)
    random_days = random.randint(0, 6)
    random_date = last_week + datetime.timedelta(days=random_days)
    random_time = datetime.time(random.randint(0, 23), random.randint(0, 59), random.randint(0, 59))
    return datetime.datetime.combine(random_date, random_time)

def _skip_save():
    pass

# Sets max size to 4MB
max_total_size = 4 * 1_000_000

for i in range(target_requests):

    output_size = random.randint(1, max_total_size)
    input_size = random.randint(1, max_total_size-output_size)

    test_time = random_date_last_week()
    command_name = random.choice(["say","dont_say","echo","test"])
    system_name = random.choice(["echo_1","echo_2","test_1","test_2"])
    system_version = random.choice(["1.0.0","2.0.0","3.0.0","4.0.0"])
    instance_name = random.choice(["default","test","test_1","test_2"])
    command_type = random.choice(["ACTION","INFO"])

    request = Request(
        namespace="generated",
        system=system_name,
        system_version=system_version,
        instance_name=instance_name,
        command=command_name,
        command_display_name=command_name,
        status="SUCCESS",
        command_type= command_type,
        comment=f"Created request {i + 1} of {target_requests}",
        parameters={"input": "".join(("a" for _ in range (input_size - sys.getsizeof(""))))},
        output="".join(("a" for _ in range (output_size - sys.getsizeof("")))),
        metadata={},
        updated_at = test_time,
        created_at = test_time
    )
    request.output_gridfs.put(b"test", filename="test.txt")
    
    # Override functions so we don't run them
    request._pre_save = _skip_save
    request._post_save = _skip_save

    request.save()
    print(f"Created request {i + 1} of {target_requests}")