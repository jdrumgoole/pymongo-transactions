# Pymongo Transactions Example Code

Example code showing the MongoDB Python driver (Pymongo) in action.

* __setup.sh__ : Configure the enviroment including downloading MongoDB
etc.
* __mongod.sh__ : Start and stop MongoDB once setup.sh is run (mongodb.sh
start|stop).
* __transaction_main.py__ : Run a set of writes with and without transactions run ```python transactions_main.py -h``` for help.
* __watch_collection.py__ : Use a mongodb changstream to watch collections
as they change when transactions_main.py is running
* __kill_primary.py__ : Starts a MongoDB replica set (on port 7100) and kills the
primary on a regular basis. Used to emulate an election happening in the middle
of a transaction.
* __featurecompatibility.py__ : check and or set feature compatibility for
  th database (needs to be set to "4.0" for transactions)

## Setting up the transactions code
The first example is for MongoDB 4.0 and shows the transactions code
in action. The ```transactions/setups.sh``` will setup your enviroment
including

* Downloading and installing MongoDB 4.0 RC7
* Setting up a python virtualenv
* Install the beta version of the Python MongoDB Driver (pymongo)
* Install mtools to allow easy starting of a
[replica set](https://docs.mongodb.com/manual/tutorial/deploy-replica-set/).
(transactions require a replica set)
* Sstart a replica set.  The replica set name is **txntest**.

All this is achieved using a single ```setup.sh``` script. 

<pre>
<b>cd transactions</b>
<b>./setup.sh</b>

<b>python transaction_main.py -h</b>
usage: transaction_main.py [-h] [--host HOST] [--usetxns] [--delay DELAY]
                           [--iterations ITERATIONS]

optional arguments:
  -h, --help                show this help message and exit
  --host HOST               MongoDB URI [default: mongodb://localhost:27017?replicaSet=txntest]
  --usetxns                 Use transactions [default: False]
  --delay DELAY             Delay between two insertion events [default: 1.0]
  --iterations ITERATIONS   Run N iterations. O means run forever
  --randdelay RANDDELAY RANDDELAY
                            Create a delay set randomly between the two bounds
                            [default: None]
  </pre>

After ```setup.sh``` has completed you can start and stop the server by
running ``mongod.sh``  with the ```start``` or ```stop``` parameter.

## Running the transactions example

The transactions example consists of two python
programs. ```transaction_main.py``` and ```watch_collection.py```.
As you can see above ```transaction_main.py``` has few options. For
local operation ```--host``` is probably not required. Note that the
program defaults to using a replicaSet **txntest** which is the
replica set name that is configured in the server in ```setup.sh```

To run the program without transactions you can run it with no arguments:

```$ source venv/bin/activate
(venv)$ python transaction_main.py
using collection: PYTHON_TXNS_EXAMPLE.seats
using collection: PYTHON_TXNS_EXAMPLE.payments
Booking seat: '1A'
Sleeping: 0.9990250744702165
Paying 500 for seat '1A'
Booking seat: '2A'
Sleeping: 0.802693439030369
Paying 500 for seat '2A'
Booking seat: '3A'
Sleeping: 0.8532081718219303
Paying 500 for seat '3A'
(venv) $
```

Now run it with transactions turned on. This is a useful test to
ensure the environment is configured correctly:

```
(venv) $ python transaction_main.py --usetxns
using collection: PYTHON_TXNS_EXAMPLE.seats
using collection: PYTHON_TXNS_EXAMPLE.payments
Using transactions
Booking seat: '1A'
Sleeping: 0.13754149185618314
Paying 500 for seat '1A'
Using transactions
Booking seat: '2A'
Sleeping: 0.35207015352640436
Paying 500 for seat '2A'
Using transactions
Booking seat: '3A'
Sleeping: 0.9508466296765761
Paying 500 for seat '3A'
(venv) $
```

To actually see the effect of transactions we need to watch what is
happening inside the collections ```PYTHON_TXNS_EXAMPLE.seats``` and ```
PYTHON_TXNS_EXAMPLE.payments```.

We can do this with ```watch_collection.py```. The uses [MongoDB
change streams](https://docs.mongodb.com/manual/changeStreams/)
to see whats happening inside a collection in real-time. We need run
two of these in parallel so its best to line them up side by side.

here is the ```watch_collection.py``` program:

```
$ python watch_collection.py
usage: watch_collection.py [-h] [--host HOST] [--watch WATCH]

optional arguments:
  -h, --help              show this help message and exit
  --host HOST          mongodb URI for connecting to server [default:
                                 mongodb://localhost:27017/?replicaSet=txntest]
  --watch WATCH     Watch <database.colection> [default: test.test]
```
  
We need to watch each collection so in each window start the watcher.

Window 1:
```
$ python watch_collection.py --watch PYTHON_TXNS_EXAMPLE.seats
Watching: PYTHON_TXNS_EXAMPLE.seats
```

Window 2:
```
$ python watch_collection.py --watch PYTHON_TXNS_EXAMPLE.payments
Watching: PYTHON_TXNS_EXAMPLE.payments
```

## What Happens when you use transactions

Lets run the code without transactions first. If you examine the
```transaction_main.py``` code you will see a function
``txn_sequence``.

```
def txn_sequence(seats, payments, seat_no, delay, session=None):
    price=500
    seat_str = "{}A".format(seat_no)
    print( "Booking seat: '{}'".format(seat_str))
    seats.insert_one({"flight_no": "EI178", "seat": seat_str, "date": datetime.utcnow()}, session=session)
    if delay > 0 :
        delay_period = random.uniform(0, delay)
        print( "Sleeping: {}".format(delay_period))
        time.sleep(delay_period)
    payments.insert_one({"flight_no": "EI178", "seat" : seat_str, "date": datetime.utcnow(), "price": price},session=session)
    print( "Paying {} for seat '{}'".format(price, seat_str))

```

This program emulates a very simplified airline booking with a seat
being allocated and then paid for. These happen at different times and
we emulate this by inserting a random delay (the default is between 1
and 3 seconds).

If we run the program without transactions then we will see these
delays reported by the ```watch_collection.py``` programs.

Now if we run the same program with the ```--usetxns``` we will see
that the change streams become synchronised because both collections
only see the changes when the `end_transaction()` call happens. In
python the ```with``` clause ensures this happens.
