from sshtunnel import SSHTunnelForwarder
import pymongo
import pprint

# ssh -i IRTG firstname_lastname@35.205.115.90

MONGO_HOST = "35.205.115.90"
MONGO_DB = "cryptocurrency"
MONGO_COLLECTION = "deribit_transactions"

server = SSHTunnelForwarder(
    MONGO_HOST,
    ssh_username="firstname_lastname",
    ssh_pkey="/Users/firstname/.ssh/IRTG",
    ssh_private_key_password="XXX",
    remote_bind_address=("127.0.0.1", 27017),
)

server.start()

client = pymongo.MongoClient("127.0.0.1", server.local_bind_port)
db = client[MONGO_DB]
pprint.pprint(db.collection_names())


def get_as_df(collection, query):
    cursor = collection.find(query)
    df = pd.DataFrame(list(cursor))
    return df


# query = {
#     "$and": [
#         {"timestamp": {"$gte": start_ts}},
#         {"timestamp": {"$lte": end_ts}},
#     ]
# }

# df_all = get_as_df(collection, query)

coll = db[MONGO_COLLECTION]
coll.find_one(sort=[("timestamp", -1)])
from datetime import datetime

datetime.fromtimestamp(1601115135255 / 1000)

coll.find_one()

server.stop()