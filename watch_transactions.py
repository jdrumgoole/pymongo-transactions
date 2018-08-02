"""
Simple program to watch a transactions collection. Defaults to the port 7100 and replica set 27100
"""
import pymongo
from argparse import ArgumentParser
from datetime import datetime
import pprint
import sys

if __name__ == "__main__":

    parser = ArgumentParser()

    parser.add_argument("--host", default="mongodb://localhost:27100/?replicaSet=txntest",
                        help="mongodb URI for connecting to server [default: %(default)s]")
    parser.add_argument("--database", default="SEATSDB", help="Watch <database.collection> [default: %(default)s]")
    parser.add_argument("--collection", default="seats", help="Watch <database.collection> [default: %(default)s]")

    args = parser.parse_args()

    client = pymongo.MongoClient(host=args.host)


    database = client[args.database]
    collection = database[args.collection]

    try:
        while True:
            print("Creating new watch cursor")
            watch_cursor = collection.watch()
            print("Watching: {}.{}\n".format(args.database, args.collection))

            for d in watch_cursor:
                if d["operationType"] == "invalidate":

                    print("Watch cursor invalidated (deleted collection?)")
                    #pprint.pprint(d)
                    print("Closing cursor")
                    watch_cursor.close()
                    break
                else:
                    del d["fullDocument"]["_id"]
                    #pprint.pprint(d)
                    print("local time   : {}".format(datetime.utcnow()))
                    print("cluster time : {}".format(d["clusterTime"].as_datetime()))
                    print("collection   : {}.{}".format(d["ns"]["db"], d["ns"]["coll"]))
                    print("doc          : {}".format(d["fullDocument"]))

    except KeyboardInterrupt:
        print("Closing watch cursor")
        watch_cursor.close()
        print("exiting...")
