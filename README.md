# Introduction to MongoDB transactions in Python 

Multi-document transactions arrived in 
[MongoDB 4.0](https://www.mongodb.com/download-center#community) in June 2018. MongoDB has always
been transactional around updates to a single document. Now, with 
multi-document transactions we can wrap a set of database operations
inside a *start* and *commit* transaction call. This ensures that even with inserts and/or
updates happening across multiple collections and/or databases, the external view of the data meets [ACID](https://en.wikipedia.org/wiki/ACID) constraints. 

To demonstrate transactions in the wild we use a trivial example app that emulates a flight 
booking for an online airline application. In this simplified booking we need to undertake three
operations:

1. Allocate a seat (**seat_collection**)
2. Pay for the seat (**payment_collection**)
3. Update the count of allocated seats and sales (**audit_collection**)

For this application we will use three separate collections for these documents as detailed in bold above. 
The code in ```transactions_main.py``` updates these collections in serial unless the ```--usetxns``` argument
is used. We then wrap the complete set of operations inside an ACID transaction. 
The code in ``transactions_main.py`` is built directly using the MongoDB Python driver 
([Pymongo 3.7.1](https://api.mongodb.com/python/current/)).
See the section on [client sessions](https://api.mongodb.com/python/current/api/pymongo/client_session.html)
for an overview of the new transactions API in 3.7.1. 

The goal of this code is to demonstrate to the Python developer just how easy it is to
covert existing code to transactions if required or to port older SQL based systems.

## Setting up your environment

The following files can be found in the associated github repo, [pymongo-transactions.](https://github.com/jdrumgoole/pymongo-transactions)

* __.gitignore__ : Standard Github __.gitignore__ for Python
* __LICENSE__ : Apache's 2.0 (standard Github) license
* __Makefile__ : Makefile with targets for default operations
* __transaction_main.py__ : Run a set of writes with and without transactions. Run 
`python transactions_main.py -h` for help.
* __transactions_retry.py__ : The file containing the transactions retry functions.
* __watch_transactions.py__ : Use a MongoDB change stream to watch collections
as they change when transactions_main.py is running
* __kill_primary.py__ : Starts a MongoDB replica set (on port 7100) and kills the
primary on a regular basis. This is used to emulate an election happening in the middle
of a transaction.
* __featurecompatibility.py__ : check and/or set feature compatibility for
  the database (it needs to be set to "4.0" for transactions)
  
you can clone this repo and work alongside us during this blog post (please file any problems on the Issues tab for the repo).

We assume for all that follows that you have [Python 3.6](https://www.python.org/downloads/) or greater correctly installed and on your path.

The `Makefile` outlines the operations that are required to setup the test
environment. 

All the programs in this example use a port range starting at **27100**
to ensure that this example does not clash with an existing MongoDB installation.

## Preparation

To setup the environment you can run through the following steps manually. People
that have `make` can speed up installation by using the ``make install`` command.

### Set a python [virtualenv](https://docs.python.org/3/library/venv.html)

<pre>
<b>$ cd pymongo-transactions
$ virtualenv -p python3 venv
$ source venv/bin/activate</b>
</pre>

### Install Python MongoDB Driver, [pymongo](https://pypi.org/project/pymongo/)

Install the latest version of the PyMongo MongoDB Driver (3.7.1 at the time of writing).

<pre>
<b>pip install --upgrade pymongo</b>
</pre>

### Install [Mtools](https://github.com/rueckstiess/mtools)

MTools is a collection of helper scripts to parse, filter, and visualize MongoDB log files 
(mongod, mongos). mtools also includes `mlaunch`, a utility to quickly set 
up complex MongoDB test environments on a local machine. For this demo we are only going to use the
[mlaunch](http://blog.rueckstiess.com/mtools/mlaunch.html) program. 

<pre>
<b>pip install mtools</b>
</pre>

the ``mlaunch`` program also requires the [psutil](https://pypi.org/project/psutil/) package. 

<pre>
<b>pip install psutil</b>
</pre>

The  ``mlaunch`` program gives us a simple command to start a MongoDB replica set as transactions
are only supported on a replica set

Start a replica set whose name is **txntest**. (see the ```make init_server``` make target)
for details:

<pre>
<b>mlaunch init --port 27100 --replicaset --name "txntest"</b>
</pre>

### Using the Makefile for configuration

There is a ```Makefile``` with targets for all these operations. For those of you on
platforms without access to Make it should be easy enough to cut and paste
the commands out of the targets and run them on the command line.

Running the ```Makefile```

<pre>
<b>cd pymongo-transactions
make</b>
</pre>

You will need to have MongoDB 4.0 on your path. There are other convenience targets for 
starting the demo programs:

* `make notxns` : start the transactions client without using transactions
* `make usetxns` : start the transactions client with transactions enabled
* `make watch_seats` : watch the seats collection changing
* `make watch_payments` : watch the payment collection changing

## Running the transactions example

The transactions example consists of two python
programs. `transaction_main.py` and `watch_transactions.py`.

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
</pre>

You can choose to use `--delay` or `--randdelay`. If you use both `--delay` takes precedence. The `--randdelay` 
parameter creates a random delay between a lower and an upper bound that will be added between each
insertion event. 

The `transactions_main.py` program knows to use the **txntest** replica set and the right default port range.

To run the program without transactions you can run it with no arguments:

<pre>
$ <b>python transaction_main.py</b>
using collection: SEATSDB.seats
using collection: PAYMENTSDB.payments
using collection: AUDITDB.audit
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

The program runs a function called `book_seat()` which books a seat on a plane
by adding documents to three collections. First it adds the seat allocation to the `seats_collection`, then
it adds a payment to the payments_collection`, finally it updates an audit count in the ```audit_collection```. 
(This is a much simplified booking process used purely for illustration).

The default is to run the program **without** using transactions. To use transactions we have to add the command line flag
`--usetxns`. Run this to test that you are running MongoDB 4.0 and that the correct 
[featureCompatibility](https://docs.mongodb.com/manual/reference/command/setFeatureCompatibilityVersion/) is
configured (it must be set to 4.0). If you install MongoDB 4.0 over an existing `/data` directory containing 3.6
databases then featureCompatibility will be set to 3.6 by default and transactions will not be available.

Note:
If you get the following error running `python transaction_main.py --usetxns` that means you are
picking up an older version of pymongo (older than 3.7.x) for which there is no multi-document transactions
support. 

<pre>
Traceback (most recent call last):
  File "transaction_main.py", line 175, in <module>
    total_delay = total_delay + run_transaction_with_retry( booking_functor, session)
  File "/Users/jdrumgoole/GIT/pymongo-transactions/transaction_retry.py", line 52, in run_transaction_with_retry
    with session.start_transaction():
AttributeError: 'ClientSession' object has no attribute 'start_transaction'
</pre>


### Watching Transactions
To actually see the effect of transactions we need to watch what is
happening inside the collections `SEATSDB.seats` and `
PAYMENTSDB.payments`.

We can do this with ```watch_transactions.py```. This script uses [MongoDB
Change Streams](https://docs.mongodb.com/manual/changeStreams/)
to see what's happening inside a collection in real-time. We need to run
two of these in parallel so it's best to line them up side by side.

Here is the ```watch_transactions.py``` program:

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
  
We need to watch each collection so in two separate terminal windows start the watcher.

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

### What Happens when you run without transactions?

Lets run the code without transactions first. If you examine the
```transaction_main.py``` code you will see a function
``book_seats``.

<pre>

def <b>book_seat</b>(seats, payments, audit, seat_no, delay_range, session=None):
    '''
    Run two inserts in sequence.
    If session is not None we are in a transaction

    :param seats: seats collection
    :param payments: payments collection
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
being allocated and then paid for. These are often separated by a reasonable time frame (e.f. seat allocation vs external
credit card validation and anti-fraud check) and
we emulate this by inserting a delay. The default is  1 second.


Now with the two ```watch_transactions.py``` scripts running for ```seats_collection``` and ```payments_collection```
we can run ```transactions_main.py``` as follows:
<pre>
$ <b>python transaction_main.py</b>
</pre>

The first run is with no transactions enabled. 

The bottom window shows ```transactions_main.py``` running. On the top left we are watching the inserts to the
seats collection. On the top right we are watching inserts to the payments collection. 

![Watching inserts without using transactions](http://developer-advocacy-public.s3.amazonaws.com/blog/txn_blog_post_notxns.png)

We can see that the payments window lags the seats window as the watchers only update when the insert is complete.
Thus seats sold cannot be easily reconciled with corresponding payments. If after the third seat has been booked we CTRL-C
the program we can see that the program exits before writing the payment. This is reflected in the Change Stream for
the payments collection which only shows payments for seat 1A and 2A versus seat allocations for 1A, 2A and 3A. 

If we want payments and seats to be instantly reconcilable and consistent we must execute the inserts inside a
transaction.

### What happens when you run with Transactions?

Now lets run the same system with ```--usetxns``` enabled. 

<pre>
$ <b>python transaction_main.py --usetxns</b>
</pre>

We run with the exact same setup but now set ```--usetxns```.

![Watching inserts using transactions](http://developer-advocacy-public.s3.amazonaws.com/blog/txn_blog_post_txns.png)

Note now how the change streams are interlocked and are updated in parallel. This is because all the updates only
become visible when the transaction is committed. Note how we aborted the third transaction by hitting CTRL-C.
Now neither the seat nor the payment appear in the change streams unlike the first example where the seat went through.

This is where transactions shine in world where all or nothing is the watchword. We never want to keeps seats allocated 
unless they are paid for. 

## What happens during failure?

In a MongoDB replica set all writes are directed to the Primary node. If the primary node fails or becomes
inaccessible (e.g. due to a network partition) writes in flight may fail. In a non-transactional scenario
the driver will recover from a single failure and [retry the write](https://docs.mongodb.com/manual/core/retryable-writes/).
In a multi-document transaction we must recover and retry in the event of these kinds of transient failures. This code is 
encapsulated in `transaction_retry.py`. We both retry the transaction and retry the commit to handle scenarios
where the primary fails within the transaction and/or the commit operation.

<pre>

def commit_with_retry(session):
    while True:
        try:
            # Commit uses write concern set at transaction start.
            session.commit_transaction()
            print("Transaction committed.")
            break
        except (pymongo.errors.ConnectionFailure, pymongo.errors.OperationFailure) as exc:
            # Can retry commit
            if exc.has_error_label("UnknownTransactionCommitResult"):
                print("UnknownTransactionCommitResult, retrying "
                      "commit operation ...")
                continue
            else:
                print("Error during commit ...")
                raise

def run_transaction_with_retry(functor, session):
    assert (isinstance(functor, Transaction_Functor))
    while True:
        try:
            with session.start_transaction():
                result=functor(session)  # performs transaction
                commit_with_retry(session)
            break
        except (pymongo.errors.ConnectionFailure, pymongo.errors.OperationFailure) as exc:
            # If transient error, retry the whole transaction
            if exc.has_error_label("TransientTransactionError"):
                print("TransientTransactionError, retrying "
                      "transaction ...")
                continue
            else:
                raise

    return result
</pre>
 

In order to observe what happens during elections we can use the script ```kill_primary.py```. This script 
will start a replica-set and continuously kill the primary. 

<pre>
$ <b>make kill_primary</b>
. venv/bin/activate && python kill_primary.py
no nodes started.
Current electionTimeoutMillis: 500
1. (Re)starting replica-set
no nodes started.
1. Getting list of mongod processes
Process list written to mlaunch.procs
1. Getting replica set status
1. Killing primary node: 31029
1. Sleeping: 1.0
2. (Re)starting replica-set
launching: "/usr/local/mongodb/bin/mongod" on port 27101
2. Getting list of mongod processes
Process list written to mlaunch.procs
2. Getting replica set status
2. Killing primary node: 31045
2. Sleeping: 1.0
3. (Re)starting replica-set
launching: "/usr/local/mongodb/bin/mongod" on port 27102
3. Getting list of mongod processes
Process list written to mlaunch.procs
3. Getting replica set status
3. Killing primary node: 31137
3. Sleeping: 1.0
</pre>

`kill_primary.py` resets [electionTimeOutMillis](https://docs.mongodb.com/manual/reference/replica-configuration/index.html)
to 500ms from its default of 10000ms (10 seconds). This allows elections
to resolve more quickly for the purposes of this test as we are running everything locally.


Once `kill_primary.py` is running
we can start up `transactions_main.py` again using the `--usetxns` argument.

<pre>
$ <b>make usetxns</b>
. venv/bin/activate && python transaction_main.py --usetxns
Forcing collection creation (you can't create collections inside a txn)
Collections created
using collection: PYTHON_TXNS_EXAMPLE.seats
using collection: PYTHON_TXNS_EXAMPLE.payments
using collection: PYTHON_TXNS_EXAMPLE.audit
Using a fixed delay of 1.0
Using transactions

1. Booking seat: '1A'
1. Sleeping: 1.000
1. Paying 440 for seat '1A'
Transaction committed.
2. Booking seat: '2A'
2. Sleeping: 1.000
2. Paying 330 for seat '2A'
Transaction committed.
3. Booking seat: '3A'
3. Sleeping: 1.000
TransientTransactionError, retrying transaction ...
3. Booking seat: '3A'
3. Sleeping: 1.000
3. Paying 240 for seat '3A'
Transaction committed.
4. Booking seat: '4A'
4. Sleeping: 1.000
4. Paying 410 for seat '4A'
Transaction committed.
5. Booking seat: '5A'
5. Sleeping: 1.000
5. Paying 260 for seat '5A'
Transaction committed.
6. Booking seat: '6A'
6. Sleeping: 1.000
TransientTransactionError, retrying transaction ...
6. Booking seat: '6A'
6. Sleeping: 1.000
6. Paying 380 for seat '6A'
Transaction committed.
<b>...</b>
</pre>

As you can see during elections the transaction will be aborted and must
be retried. If you look at the `transaction_rety.py` code you
will see how this happens. If a write operation encounters an error it will throw  one of the
following exceptions:

* [pymongo.errors.ConnectionFailure](http://api.mongodb.com/python/current/api/pymongo/errors.html)
* [pymongo.errors.OperationFailure](http://api.mongodb.com/python/current/api/pymongo/errors.html)

Within these exceptions there will be a label called [TransientTransactionError](https://docs.mongodb.com/manual/core/transactions/#transactions-and-mongodb-drivers).
This label can be detected using the *has_error_label(label)* function which is available
in pymongo 3.7.x. Transient errors can be recovered from and the retry code in `transactions_retry.py`
has code that retries for both writes and commits (see above). 

## Conclusions

Multi-document transactions are the final piece of the jigsaw for SQL developers who have been shying away from trying 
MongoDB. ACID transactions make the programmer's job easier and give teams that are migrating from an existing
SQL schema a much more consistent and convenient transition path.

As most migrations involving a move from highly normalised data structures to more natural and flexible nested JSON documents
one would expect that the number of required multi-document transactions will be less in a properly
constructed MongoDB application. But where multi-document transactions are required programmers can 
now include them using very similar syntax to SQL.

With ACID transactions in MongoDB 4.0 it can now be the first choice for an even broader range of 
application use cases. 

Why not try our transactions today by setting up your first cluster on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) our Database as a Service 
offering.

To try it locally [download MongoDB 4.0](https://www.mongodb.com/download-center#production).

 
