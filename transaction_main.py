"""
Program to demo Transactions in MongoDB 4.0.

@Author: Joe.Drumgoole@mongodb.com

"""
from argparse import ArgumentParser
import datetime
import time
import sys
import random
import pymongo
import pymongo.errors

from transaction_retry import Transaction_Functor, run_transaction_with_retry, commit_with_retry

def count(i,s):
    return "{}. {}".format(i,s)

def create(database, collection_name):
    """
    Force creation of a collection.
    :param database: a MongoDB database object
    :param collection_name: the name of the new collection
    :return collection: a MongoDB collection
    """

    return pymongo.collection.Collection(database=database, name=collection_name, create=True)


def end_report(usetxns, audit_collection, total_delay):
    end = datetime.datetime.utcnow()
    time_delta_delay = datetime.timedelta(seconds=total_delay)
    duration = end - start
    actual_time = duration - time_delta_delay
    print("")
    doc = audit_collection.find_one( { "audit" :"seats"})
    if usetxns:
        print("No. of ACID txns        : {}".format( doc["count"] ))
    else:
        print("No. of non ACID txns    : {}".format( doc["count"] ))

    print("Elaped time             : {}".format(duration))
    print("Average txn time        : {}".format( actual_time / i))
    print("Delay overhead          : {}".format(time_delta_delay))
    print("Actual time             : {}".format( actual_time))

def book_seat(seats, payments, audit, seat_no, delay_range, session=None):
    '''
    Run three inserts in sequence.
    If session is not None we are in a transaction

    :param seats: seats collection
    :param payments: payments collection
    :param audit: audit collection
    :param seat_no: the number of the seat to be booked (defaults to row A)
    :param delay_range: A tuple indicating a random delay between two ranges or a single float fixed delay
    :param session: Session object required by a MongoDB transaction
    :return: the delay_period for this transaction
    '''
    price = random.randrange(200, 500, 10)
    if type(delay_range) == tuple:
        delay_period = random.uniform(delay_range[0], delay_range[1])
    else:
        delay_period = delay_range

    # Book Seat
    seat_str = "{}A".format(seat_no)
    print(count( i, "Booking seat: '{}'".format(seat_str)))
    seats.insert_one({"flight_no" : "EI178",
                      "seat"      : seat_str,
                      "date"      : datetime.datetime.utcnow()},
                     session=session)
    print(count( seat_no, "Sleeping: {:02.3f}".format(delay_period)))
    #pay for seat
    time.sleep(delay_period)
    payments.insert_one({"flight_no" : "EI178",
                         "seat"      : seat_str,
                         "date"      : datetime.datetime.utcnow(),
                         "price"     : price},
                        session=session)
    print(count(seat_no, "Paying {} for seat '{}'".format(price, seat_str)))
    audit.update_one({ "audit" : "seats"}, { "$inc" : { "count" : 1}}, upsert=True, session=session)

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
    seatsdb = client["SEATSDB"]
    paymentsdb = client["PAYMENTSDB"]
    auditdb = client[ "AUDITDB"]
    payments_collection = paymentsdb["payments"]
    seats_collection = seatsdb["seats"]
    audit_collection = auditdb["audit"]
    payments_collection.drop()
    seats_collection.drop()
    audit_collection.drop()

    if args.usetxns:
        print("Forcing collection creation (you can't create collections inside a txn)")
        seats_collection    = create(seatsdb, "seats")
        payments_collection = create(paymentsdb, "payments")
        audit_collection    = create(auditdb, "audit")
        print("Collections created")

    print("using collection: {}.{}".format(seatsdb.name, seats_collection.name))
    print("using collection: {}.{}".format(paymentsdb.name, payments_collection.name))
    print("using collection: {}.{}".format(auditdb.name, audit_collection.name))

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
        print("(This happens if you run mongod 4.0 and point it at data directory created with")
        print(" an older version of mongod)")
        print("You need to set featureCompatibility to '4.0'")
        print("run 'python3 featurecompatibility.py --feature_version 4.0'")
        sys.exit(1)

    if args.randdelay:
        delay = (args.randdelay[0], args.randdelay[1])
        print("Using a random delay between {} and {}".format(args.randdelay[0], args.randdelay[1]))
    else:
        print("Using a fixed delay of {}".format(args.delay))
        delay = args.delay


    total_delay = 0

    if args.usetxns:
        print("Using transactions")

    i = 0
    print("")
    start = datetime.datetime.utcnow()
    try:
        while True:
            if (args.iterations > 0) and (i == args.iterations):
                break

            i = i + 1

            booking_functor = Transaction_Functor(book_seat,
                                                  seats_collection,
                                                  payments_collection,
                                                  audit_collection,
                                                  i, delay)

            if args.usetxns:
                # If you were looping over txns in real-life you would reuse the session for all
                # the transactions in the loop
                #
                with client.start_session() as session:
                    total_delay = total_delay + run_transaction_with_retry( booking_functor, session)
            else:
                total_delay = total_delay + booking_functor()

    except KeyboardInterrupt:

        end_report(args.usetxns, audit_collection, total_delay)
        print("Exiting due to interrupt..." )
        sys.exit(1)

    end_report(args.usetxns, audit_collection, total_delay)
