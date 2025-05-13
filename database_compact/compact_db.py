from beer_garden.db.mongo.api import check_connection, create_connection
from mongoengine.connection import get_db

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
create_connection(db_config=db_config)
check_connection(db_config)

db = get_db()


def get_stats(collection_name):
    stats = db.command({"collStats": collection_name})
    return {
        "count": stats["count"],
        "size": stats["size"],
        "storageSize": stats["storageSize"],
        "nindexes": stats["nindexes"],
        "totalIndexSize": stats["totalIndexSize"],
    }


# mongod rebuilds all indexes in parallel following the compact operation.
for collection_name in db.list_collection_names():
    print(f"Compacting: {collection_name}")
    stats = db.command({"collStats": collection_name})
    print(f"Before {collection_name} compact: {get_stats(collection_name)}")
    db.command({"compact": collection_name})
    print(f"After {collection_name} compact: {get_stats(collection_name)}")
