#
# Commands to setup the transactions demo code for Python and  MongoDB 4.0
#
# @author: Joe.Drumgoole@mongodb.com
#
PIPBIN=`which pip`

install:version_check virtualenv pip_reqs init_server
	@echo "Transactions test environment ready"

init_server:
	@if [ ! -d "data" ];then\
		echo "Making new mlaunch environment in 'data'";\
		mlaunch init --port 27100 --replicaset --name "txntest";\
	fi

start_server:
	@if [ -d "data" ];then\
		echo "Starting mongod replica set";\
		sh mongod.sh start;\
	fi

stop_server:
	@if [ -d "data" ];then\
		echo "Starting mongod replica set";\
		sh mongod.sh stop;\
	fi

pip_check:
	@if [ "${PIPBIN}" = "" ];then\
		echo "pip is not installed. Please install using instructions from:";\
		echo "https://pip.pypa.io/en/stable/installing/";\
		python3 -m webbrowser -t  "https://pip.pypa.io/en/stable/installing/";\
	fi
pip_reqs:
	(source venv/bin/activate && pip3 install -r requirements.txt)

virtualenv:
	@if [ ! -d "venv" ];then\
		echo "making virtualenv in 'venv'";\
		python3 -m venv venv;\
	fi

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
