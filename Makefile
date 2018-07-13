#
# Commands to setup the transactions demo code for Python and  MongoDB 4.0
#
# @author: Joe.Drumgoole@mongodb.com
#
PIPBIN=`which pip3 2>/dev/null`
MONGODBBIN=/usr/local/mongodb/bin

install:version_check virtualenv pip_reqs init_server
	@echo "Transactions test environment ready"

init_server: pip_check
	@echo "Setting up replica set";\
	if [ -d "data" ];then\
		echo "Already configured in 'data'";\
	else\
		echo "Making new mlaunch environment in 'data'";\
		mlaunch init --binarypath ${MONGODBBIN} --port 27100 --replicaset --name "txntest";\
	fi

start_server:
	@echo "Starting MongoDB replica set"
	@if [ -d "data" ];then\
		mlaunch start;\
	else\
		echo "No mlaunch data, run make init_server";\
	fi

stop_server:
	@echo "Stopping MongoDB replica set"
	@if [ -d "data" ];then\
		mlaunch stop;\
	else\
		echo "No mlaunch data, run make init_server";\
	fi

pip_check:
	@echo "Checking that pip3 is installed"
	@if [ "${PIPBIN}" = "" ];then\
		echo "pip3 is not installed. Please install using instructions from:";\
		echo "https://pip.pypa.io/en/stable/installing/";\
		python3 -m webbrowser "https://pip.pypa.io/en/stable/installing/";\
		exit 1;\
	fi

pip_reqs: pip_check virtualenv
	@echo "Installing required python tools and packages"
	@(. venv/bin/activate && pip3 install -r requirements.txt)

virtualenv:
	@if [ ! -d "venv" ];then\
		echo "making virtualenv in 'venv'";\
		python3 -m venv venv;\
	fi

#mtools dir and virtualenv
clean: stop_server
	rm -rf data venv req_installed


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
	@echo "You can download the latest version of MongoDB from https://www.mongodb.com/download-center?jmp=nav#community"
	@python -m webbrowser "https://www.mongodb.com/download-center#production"
