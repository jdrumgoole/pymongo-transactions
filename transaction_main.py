"""
Program to demon Transactions in MongoDB 4.x.

@Author: Joe.Drumgoole@mongodb.com

"""
from argparse import ArgumentParser
import datetime
import time
import sys
import random
import pymongo.errors

def count(i,s):
    return "{}. {}".format(i,s)

def touch(collection):
    """
    Force creation of a replica set by creating and deleting a doc.
    :param collection:
    :return collection:
    """
    doc={}
    collection.insert_one(doc)
    collection.delete_one(doc)
    return collection

def txn_sequence(seats, payments, seat_no, delay_range, session=None):
    price = random.randrange(200, 500, 10)
    seat_str = "{}A".format(seat_no)
    print(count( i, "Booking seat: '{}'".format(seat_str)))
    seats.insert_one({"flight_no": "EI178", "seat": seat_str, "date": datetime.datetime.utcnow()}, session=session)

    if type(delay_range) == tuple:
        delay_period = random.uniform(delay_range[0], delay_range[1])
    else:
        delay_period = delay_range

    print(count( seat_no, "Sleeping: {:02.3f}".format(delay_period)))
    time.sleep(delay_period)

    payments.insert_one({"flight_no": "EI178", "seat": seat_str, "date": datetime.datetime.utcnow(), "price": price},
                        session=session)
    print(count(seat_no, "Paying {} for seat '{}'".format(price, seat_str)))

    return delay_period

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("--host", default="mongodb://localhost:27100,localhost:27101,localhost:27102/?replicaSet=txntest&retryWrites=true",
                        help="MongoDB URI [default: %(default)s]")
    parser.add_argument("--usetxns", default=False, action="store_true", help="Use transactions [default: %(default)s]")
    parser.add_argument("--delay", default=1.0, type=float,
                        help="Delay between two insertion events [default: %(default)s]")
    parser.add_argument("--iterations", default=0, type=int, help="Run  N iterations. O means run forever")
    parser.add_argument("--randdelay", type=float, nargs=2,
                        help="Create a delay set randomly between the two bounds [default: %(default)s]")
    args = parser.parse_args()

    client = pymongo.MongoClient(host=args.host)
    database = client["PYTHON_TXNS_EXAMPLE"]
    payments_collection = database["payments"]
    seats_collection = database["seats"]
    print("using collection: {}.{}".format(database.name, seats_collection.name))
    print("using collection: {}.{}".format(database.name, payments_collection.name))

    print("Forcing collection creation (you can't create collections inside a txn)")
    touch(seats_collection)
    touch(payments_collection)
    print("Collections created")

    server_info = client.server_info()
    major_version = int(server_info['version'].partition(".")[0])
    if major_version < 4:
        print("The program requires MongoDB Server version 4.x or greater")
        print("You are running: mongod '{}'".format(server_info['version']))
        print("get the latest version at https://www.mongodb.com/download-center#community")
        sys.exit(1)

    doc = client.admin.command({"getParameter": 1, "featureCompatibilityVersion": 1})
    if doc["featureCompatibilityVersion"]["version"] != "4.0":
        print("Your mongod is set to featureCompatibility: {}".format(doc["featureCompatibilityVersion"]["version"]))
        print("(This happens if you run mongod and point it at data directory created with")
        print(" an older version of mongod)")
        print("You need to set featureCompatibility to '4.0'")
        print("run 'python featurecompatbility.py --feature_version 4.0'")

    if args.randdelay:
        delay = (args.randdelay[0], args.randdelay[1])
        print("Using a random delay between {} and {}".format(args.randdelay[0], args.randdelay[1]))
    else:
        print("Using a fixed delay of {}".format(args.delay))
        delay = args.delay

    print("")
    start = datetime.datetime.utcnow()
    total_delay = 0

    if args.usetxns:
        print("Using transactions")

    for i in range(1, args.iterations + 1):
        if args.usetxns:
            # If you were looping over txns in real-life you would reuse the session for all
            # the transactions in the loop
            #
            s=client.start_session()
            try:
                with s.start_transaction():
                    total_delay = total_delay + txn_sequence(seats_collection, payments_collection, i, delay, s)

            except (pymongo.errors.OperationFailure,
                    pymongo.errors.ConnectionFailure) as exc:
                if exc.has_label("TemporaryTxnFailure"):
                    print(count(i, "{} TemporaryTxnFailure".format( ">" * 20 )))
                    with s.start_transaction():
                        total_delay = total_delay + txn_sequence(seats_collection, payments_collection, i, delay, s)
                else:
                    raise

            except pymongo.errors.ConnectionFailure as e:
                print(count(i, "{} ConnectionFailure".format( ">" * 20 )))
                with s.start_transaction():
                    total_delay = total_delay + txn_sequence(seats_collection, payments_collection, i, delay, s)

            s.end_session()
        else:
            total_delay = total_delay + txn_sequence(seats_collection, payments_collection, i, delay)

    end = datetime.datetime.utcnow()
    time_delta_delay = datetime.timedelta(seconds=total_delay)
    duration = end - start
    actual_time = duration - time_delta_delay

    print("")
    print("No of transactions: {}".format( i ))
    print("Elaped time       : {}".format(duration))
    print("Average txn time  : {}".format( actual_time / i))
    print("Delay overhead    : {}".format(time_delta_delay))
    print("Actual time       : {}".format( actual_time))
