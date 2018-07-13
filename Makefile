#
# Commands to setup the transactions demo code for Python and  MongoDB 4.0
#
# @author: Joe.Drumgoole@mongodb.com
#
PIPBIN=`which pip`

install:version_check venv pip_reqs init_server
	@echo "Transactions test environment ready"

init_server:
	mlaunch init --port 27100 --replicaset --name "txntest"

start_server:
	sh mongod.sh start

stop_server:
	sh mongod.sh stop

pip_reqs:
	(source venv/bin/activate && pip3 install -r requirements.txt)

venv:
	python3 -m venv venv

#mtools dir and virtualenv
clean:
	rm -rf data venv

start:
	sh mongod.sh start

stop:
	sh mongod.sh stop

killer:
	python3 kill_primary.py

notxns:
	python3 transaction_main.py

usetxns:
	python3 transaction_main.py --usetxns

version_check:
	python3 version_check.py 3

watch_seats:
	python3 watch_transactions.py --collection seats

watch_payments:
	python3 watch_transactions.py --collection payments

download:
	echo "You can download the latest version of MongoDB from https://www.mongodb.com/download-center?jmp=nav#community"
	python -m webbrowser "https://www.mongodb.com/download-center?jmp=nav#community"
