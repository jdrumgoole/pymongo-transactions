# Introduction to MongoDB transactions in Python 

Multi-document transactions landed in 
[MongoDB 4.0](https://www.mongodb.com/download-center#community). MongoDB has always
been transactional around updates to a single document but with 
multi-document transctions we can now wrap a set of database operations
inside a begin and end transaction call. This ensure that even with inserts and/or
updates happening in multiple collections the external view of the data meets [ACID](https://en.wikipedia.org/wiki/ACID) constraints. 

To demonstrae transactions in action we use a trivial example app that emulates a flight 
booking for an online airline application. In this simplified booking we need to undertake two
operations:

1. Allocate a seat
2. Pay for a the seat



Example code showing the MongoDB []Python driver (Pymongo 3.7.0) in action.

* __setup.sh__ : Configure the enviroment including downloading MongoDB
etc.
* __mongod.sh__ : Start and stop MongoDB once setup.sh is run (mongodb.sh
start|stop).
* __transaction_main.py__ : Run a set of writes with and without transactions run ```python transactions_main.py -h``` for help.
* __watch_transactions.py__ : Use a mongodb changstream to watch collections
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

* Downloading and installing MongoDB 4.0
* Setting up a python virtualenv
* Install the latest version of the Python MongoDB Driver (pymongo 3.7.0)
* Install mtools to allow easy starting of a
[replica set](https://docs.mongodb.com/manual/tutorial/deploy-replica-set/).
(transactions require a replica set)
* Sstart a replica set.  The replica set name is **txntest**.

All this is achieved using a single ```setup.sh``` script. 

<pre>
<b>$ sh setup.sh</b>
Download mongodb
--2018-07-09 10:52:09--  https://fastdl.mongodb.org/osx/mongodb-osx-ssl-x86_64-4.0.0.tgz
Resolving fastdl.mongodb.org... 13.32.67.173, 13.32.67.249, 13.32.67.52, ...
Connecting to fastdl.mongodb.org|13.32.67.173|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 69563250 (66M) [application/x-gzip]
Saving to: 'mongodb-osx-ssl-x86_64-4.0.0.tgz'

mongodb-osx-ssl-x86 100%[=====================>]  66.34M  7.06MB/s   in 19s

2018-07-09 10:52:29 (3.46 MB/s) - 'mongodb-osx-ssl-x86_64-4.0.0.tgz' saved [69563250/69563250]

unpack mongodb
mongodb-osx-x86_64-4.0.0/README
mongodb-osx-x86_64-4.0.0/THIRD-PARTY-NOTICES
mongodb-osx-x86_64-4.0.0/MPL-2
mongodb-osx-x86_64-4.0.0/GNU-AGPL-3.0
mongodb-osx-x86_64-4.0.0/LICENSE-Community.txt
mongodb-osx-x86_64-4.0.0/bin/mongodump
mongodb-osx-x86_64-4.0.0/bin/mongorestore
mongodb-osx-x86_64-4.0.0/bin/mongoexport
mongodb-osx-x86_64-4.0.0/bin/mongoimport
mongodb-osx-x86_64-4.0.0/bin/mongostat
mongodb-osx-x86_64-4.0.0/bin/mongotop
mongodb-osx-x86_64-4.0.0/bin/bsondump
mongodb-osx-x86_64-4.0.0/bin/mongofiles
mongodb-osx-x86_64-4.0.0/bin/mongoreplay
mongodb-osx-x86_64-4.0.0/bin/mongod
mongodb-osx-x86_64-4.0.0/bin/mongos
mongodb-osx-x86_64-4.0.0/bin/mongo
mongodb-osx-x86_64-4.0.0/bin/install_compass
Checking python version
Running python Python 3.6.5
setup virtual env in venv
Collecting mtools
  Downloading https://files.pythonhosted.org/packages/f2/07/6cad9445d7bf331f21c969f045b1da76cb2e943a51dd0e2eb83f0a6d9fc9/mtools-1.5.1.tar.gz (2.9MB)
    100% |████████████████████████████████| 2.9MB 564kB/s
Collecting six (from mtools)
  Using cached https://files.pythonhosted.org/packages/67/4b/141a581104b1f6397bfa78ac9d43d8ad29a7ca43ea90a2d863fe3056e86a/six-1.11.0-py2.py3-none-any.whl
Collecting python-dateutil==2.7 (from mtools)
  Using cached https://files.pythonhosted.org/packages/bc/c5/3449988d33baca4e9619f49a14e28026399b0a8c32817e28b503923a04ab/python_dateutil-2.7.0-py2.py3-none-any.whl
Installing collected packages: six, python-dateutil, mtools
  Running setup.py install for mtools ... done
Successfully installed mtools-1.5.1 python-dateutil-2.7.0 six-1.11.0
You are using pip version 9.0.3, however version 10.0.1 is available.
You should consider upgrading via the 'pip install --upgrade pip' command.
Collecting psutil
  Using cached https://files.pythonhosted.org/packages/51/9e/0f8f5423ce28c9109807024f7bdde776ed0b1161de20b408875de7e030c3/psutil-5.4.6.tar.gz
Installing collected packages: psutil
  Running setup.py install for psutil ... done
Successfully installed psutil-5.4.6
You are using pip version 9.0.3, however version 10.0.1 is available.
You should consider upgrading via the 'pip install --upgrade pip' command.
Installing pymongo driver
Collecting https://github.com/mongodb/mongo-python-driver/archive/3.7.0b0.tar.gz
  Downloading https://github.com/mongodb/mongo-python-driver/archive/3.7.0b0.tar.gz
     | 686kB 13.4MB/s
Installing collected packages: pymongo
  Running setup.py install for pymongo ... done
Successfully installed pymongo-3.7.0b0
You are using pip version 9.0.3, however version 10.0.1 is available.
You should consider upgrading via the 'pip install --upgrade pip' command.
Initalising replica set
launching: "mongod" on port 27100
launching: "mongod" on port 27101
launching: "mongod" on port 27102
replica set 'txntest' initialized.
$
</pre>

After ```setup.sh``` has completed you can start and stop the server by
running ``mongod.sh``  with the ```start``` or ```stop``` parameter. The ``mongod,sh``
program knows the name of the replica set (**txntest**) and the port number range (27100 to 2701)

## Running the transactions example

The transactions example consists of two python
programs. ```transaction_main.py``` and ```watch_transactions.py```.

### Running transactions_main.py
<pre>
$ <b>python transaction_main.py -h</b>
usage: transaction_main.py [-h] [--host HOST] [--usetxns] [--delay DELAY]
                           [--iterations ITERATIONS]
                           [--randdelay RANDDELAY RANDDELAY]

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           MongoDB URI [default: mongodb://localhost:27100,localh
                        ost:27101,localhost:27102/?replicaSet=txntest&retryWri
                        tes=true]
  --usetxns             Use transactions [default: False]
  --delay DELAY         Delay between two insertion events [default: 1.0]
  --iterations ITERATIONS
                        Run N iterations. O means run forever
  --randdelay RANDDELAY RANDDELAY
                        Create a delay set randomly between the two bounds
                        [default: None]
$
</pre>

You can choose to use ``--delay`` or ``--randdelay`` if you use both ``--delay`` takes precedence. the ``--randdelay``
parameter creats a random delay between a lower and an upperbound that will be added between each
insertion event. 

The ``transactions_main.py`` program knows to use the **txntest** replica set and the right default port range.

To run the program without transactions you can run it with no arguments:

<pre>
$ <b>source venv/bin/activate</b>
$ <b>python transaction_main.py</b>
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
$
</pre?

Now run it with transactions turned on. This is a useful test to
ensure the environment is configured correctly:

```
(venv) $ python3 transaction_main.py --iterations 3 --usetxns
using collection: PYTHON_TXNS_EXAMPLE.seats
using collection: PYTHON_TXNS_EXAMPLE.payments
Forcing collection creation (you can't create collections inside a txn)
Collections created
Using a fixed delay of 1.0

Using transactions
1. Booking seat: '1A'
1. Sleeping: 1.000
1. Paying 430 for seat '1A'
2. Booking seat: '2A'
2. Sleeping: 1.000
2. Paying 490 for seat '2A'
3. Booking seat: '3A'
3. Sleeping: 1.000
3. Paying 320 for seat '3A'

No of transactions: 3
Elaped time       : 0:00:03.026337
Average txn time  : 0:00:00.008779
Delay overhead    : 0:00:03
Actual time       : 0:00:00.026337
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
```

This program emulates a very simplified airline booking with a seat
being allocated and then paid for. These happen at different times and
we emulate this by inserting a random delay (the default is between 1
and 3 seconds).

If we run the program without transactions then we will see these
delays reported by the ```watch_transactions.py``` programs.

Now if we run the same program with the ```--usetxns``` we will see
that the change streams become synchronised because both collections
only see the changes when the `end_transaction()` call happens. In
python the ```with``` clause ensures this happens.
