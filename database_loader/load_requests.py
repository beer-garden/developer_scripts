from beer_garden.db.mongo.models import Request
from beer_garden.db.mongo.api import check_connection, create_connection

import datetime
import random

# Set how many requests you want generated
target_requests = 10000

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
    last_week = today - datetime.timedelta(days=7)
    random_days = random.randint(0, 6)
    random_date = last_week + datetime.timedelta(days=random_days)
    random_time = datetime.time(random.randint(0, 23), random.randint(0, 59), random.randint(0, 59))
    return datetime.datetime.combine(random_date, random_time)

def _skip_save():
    pass

for i in range(target_requests):

    test_time = random_date_last_week()
    request = Request(
        namespace="generated",
        system="echo",
        system_version="latest",
        instance_name="default",
        command="say",
        status="SUCCESS",
        command_type= "ACTION",
        comment=f"Created request {i + 1} of {target_requests}",
        output="",
        metadata={},
        updated_at = test_time,
        created_at = test_time
    )
    
    # Override functions so we don't run them
    request._pre_save = _skip_save
    request._post_save = _skip_save

    request.save()
    print(f"Created request {i + 1} of {target_requests}")