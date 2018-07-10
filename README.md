# Introduction to MongoDB transactions in Python 

Multi-document transactions arrived in 
[MongoDB 4.0](https://www.mongodb.com/download-center#community) which is now shipping. MongoDB has always
been transactional around updates to a single document but with 
multi-document transctions we can now wrap a set of database operations
inside a begin and commit transaction call. This ensures that even with inserts and/or
updates happening in multiple collections the external view of the data meets [ACID](https://en.wikipedia.org/wiki/ACID) constraints. 

To demonstrae transactions in action we use a trivial example app that emulates a flight 
booking for an online airline application. In this simplified booking we need to undertake three
operations:

1. Allocate a seat (**seat_collection**)
2. Pay for a the seat (**payment_collection**)
3. Update the count of allocated seats and transactions (**audit_collection**)

For this application we will use three seperate collections for these documents as detailed in bold above. 
The code in ```transactions_main.py``` updates these collections in serial unless the ```--usetxns``` argument
is used. We then wrap the complete operation inside an ACID transaction. 
the code in ``transactions_main.py`` is built directly using the MongoDB Python driver 
([Pymongo 3.7.0](https://api.mongodb.com/python/current/)).
See the section on [client sessions](https://api.mongodb.com/python/current/api/pymongo/client_session.html)
for an overview of the new transactions API in 3.7.0.

## Configure the Environment

The following files can be found in the associated github repo, [pymongo-transactions.](https://github.com/jdrumgoole/pymongo-transactions)
you can clone this repo and work alongside us during this blog post (please file any problems on the Issues tab for the repo)

We assume for all that follows that you have Python 3.6 correctly installed and on your path.

* __.gitignore__ : Standard Github __.gitignore__ for Python
* __LICENSE__ : Apaches 2.0 (standard Github) license
* __Makefile__ : Makefile with targets for default operations
* __setup.sh__ : Configure the enviroment including downloading MongoDB
etc.
* __mongod.sh__ : Start and stop MongoDB once setup.sh is run (mongodb.sh
start|stop).
* __transaction_main.py__ : Run a set of writes with and without transactions run 
```python transactions_main.py -h``` for help.
* __transactions_retry.py__ : The file containing the transactions retry functions.
* __watch_transactions.py__ : Use a mongodb changstream to watch collections
as they change when transactions_main.py is running
* __kill_primary.py__ : Starts a MongoDB replica set (on port 7100) and kills the
primary on a regular basis. Used to emulate an election happening in the middle
of a transaction.
* __featurecompatibility.py__ : check and or set feature compatibility for
  th database (needs to be set to "4.0" for transactions)

##Setting up your environment

The ```transactions/setups.sh``` will setup your enviroment
including:

* Downloading and installing [MongoDB 4.0](https://www.mongodb.com/download-center?jmp=nav#community)
* Setting up a python [virtualenv](https://docs.python.org/3/library/venv.html)
* Installing the latest version of the Python MongoDB Driver (pymongo 3.7.0)
* Installing [mtools](https://github.com/rueckstiess/mtools) to allow easy starting of a
[replica set](https://docs.mongodb.com/manual/tutorial/deploy-replica-set/).
(transactions require a replica set)
* Start a replica set whose name is **txntest**.

All this is achieved by running  ```sh setup.sh``` script. 

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

There is a ````Makefile```` with targets for all these operations.

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
$ <b>python transaction_main.py</b>
using collection: PYTHON_TXNS_EXAMPLE.seats
using collection: PYTHON_TXNS_EXAMPLE.payments
using collection: PYTHON_TXNS_EXAMPLE.audit
Using a fixed delay of 1.0

1. Booking seat: '1A'
1. Sleeping: 1.000
1. Paying 330 for seat '1A'
2. Booking seat: '2A'
2. Sleeping: 1.000
2. Paying 450 for seat '2A'
3. Booking seat: '3A'
3. Sleeping: 1.000
3. Paying 490 for seat '3A'
4. Booking seat: '4A'
4. Sleeping: 1.000
^C
</pre>

the program runs a function called ````txn_sequence()```` which books a seat on a plane
by adding documents to three collections. First it adds the seat allocation to the ```seats_collection```, then
it adds a payment to the ```payments_collection``` finally it updates an audit count in the ```audit_collection```. 
(This is a much simplified booking process used purely for illustration).

The default is to run the program without using transactions. To use transactions we have to add the command line flag
```--usetxns```. Run this to test that you are running MongoDB 4.0 and that the correct feature 
[featureCompatibility](https://docs.mongodb.com/manual/reference/command/setFeatureCompatibilityVersion/) is
configured (it must be set to 4.0). If you install MongoDB 4.0 over an existing ```/data``` directory containing 3.6
databases then featureCompatibility will be set to 3.6 by default and transactions will not be available.```

To actually see the effect of transactions we need to watch what is
happening inside the collections ```PYTHON_TXNS_EXAMPLE.seats``` and ```
PYTHON_TXNS_EXAMPLE.payments```.

We can do this with ```watch_transactions.py```. The uses [MongoDB
change streams](https://docs.mongodb.com/manual/changeStreams/)
to see whats happening inside a collection in real-time. We need run
two of these in parallel so its best to line them up side by side.

here is the ```watch_transactions.py``` program:

<pre>
$ <b>python watch_transactions.py -h</b>
usage: watch_transactions.py [-h] [--host HOST] [--collection COLLECTION]

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           mongodb URI for connecting to server [default:
                        mongodb://localhost:27100/?replicaSet=txntest]
  --collection COLLECTION
                        Watch <database.collection> [default:
                        PYTHON_TXNS_EXAMPLE.seats_collection]
</pre>
  
We need to watch each collection so in each window start the watcher.

Window 1:
<pre>
$ <b>python watch_transactions.py --watch seats</b>
Watching: seats
...
</pre>

Window 2:
<pre>
$ <b>python watch_transactions.py --watch payments</b>
Watching: payments
...
</pre>

## What Happens when you run without transactions?

Lets run the code without transactions first. If you examine the
```transaction_main.py``` code you will see a function
``book_seats``.

<pre>

def <b>book_seat</b>(seats, payments, audit, seat_no, delay_range, session=None):
    '''
    Run two inserts in sequence.
    If session is not None we are in a transaction

    :param seats: seats collection
    :param payments: payments colection
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
    audit.update_one({ "audit" : "seats"}, { "$inc" : { "count" : 1}}, upsert=True)
    print(count(seat_no, "Paying {} for seat '{}'".format(price, seat_str)))

    return delay_period

</pre>

This program emulates a very simplified airline booking with a seat
being allocated and then paid for. These are often seperated by a reasonable time frame (e.f. seat allocation vs external
credit card validation and anti-fraud check) and
we emulate this by inserting a random delay. The default is  1 second.


Now with the two ```watch_transactions.py``` scripts running for ```seats_collection``` and ```payments_collection```
we can run ```transactions_main.py``` as follows:
<pre>
$ <b>python transaction_main.py --delay 2</b>
</pre>

The first run is with no transactions enabled. We have added a delay of 2 seconds
between the seat and payment insert operations in ``transactions_main.py`` so we can see the delay clearly. 

The bottom window shows ```transactions_main.py``` running. On the top left we are watching the inserts to the
seats collection. On the top right we are watching inserts to the payments collection. 

![Watching inserts without using transactions](http://developer-advocacy-public.s3.amazonaws.com/blog/txn_blog_post_notxns.png)

We can see that the payments window lags the seats window as the watchers only update when the insert is complete.
Thus seats sold cannot be easily reconciled with corresponding payments. If after the third seat has been booked we CTRL-C
the program we can see that the program exits before writing the payment. This is reflected in the change-stream for
payments collection which only shows payments for seat 1A and 2A versus seat allocations for 1A, 2A and 3A. 

If we want payments and seats to be instantly reconcliable and consistent we must execute the inserts inside a
transaction.

## What happens when you run with Transactions?

Now lets run the same system with ```--usetxns``` enabled. 

<pre>
$ <b>python transaction_main.py --delay 2 --usetxns</b>
</pre>

We run with the exact same setup but now set ```--usetxns```.

![Watching inserts without using transactions](http://developer-advocacy-public.s3.amazonaws.com/blog/txn_blog_post_txns.png)

Note now how the change streams are interlocked and are updated in parallel. This is because all the updates only
become visible when the transaction is committed. Note how we aborted the third transaction by hitting CTRL-C.
Now neither the seat nor the payment appear in the change streams unlike the first example where the seat went through.

This is where transactions shine in world where all or nothing is the watchword. We never want to keeps seats allocated 
unless they are paid for. 

Now if we run the same program with the ```--usetxns``` we will see
that the change streams become synchronised because both collections
only see the changes when the `end_transaction()` call happens. In
python the ```with``` clause ensures this happens.
