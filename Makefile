#
# Commands to setup the transactions demo code for Python and  MongoDB 4.0
#
# @author: Joe.Drumgoole@mongodb.com
#
PIPBIN=`which pip 2>/dev/null`
MONGODBBIN=`which mongod | xargs dirname 2>/dev/null`

install:version_check virtualenv pip_reqs init_server
	@echo "Transactions test environment ready"

init_server: pip_check mongod_check
	@echo "Setting up replica set";\
	if [ -d "data" ];then\
		echo "Already configured in 'data'";\
	else\
		echo "Making new mlaunch environment in 'data'";\
		. venv/bin/activate && mlaunch init --binarypath ${MONGODBBIN} --port 27100 --replicaset --name "txntest";\
	fi

start_server: mongod_check
	@echo "Starting MongoDB replica set"
	@if [ -d "data" ];then\
		. venv/bin/activate && mlaunch start;\
	else\
		echo "No mlaunch data, run make init_server";\
	fi

stop_server:
	@echo "Stopping MongoDB replica set"
	@if [ -d "data" ];then\
		. venv/bin/activate && mlaunch stop;\
	else\
		echo "No mlaunch data, run make init_server";\
	fi

pip_check:
	@echo "Checking that pip is installed"
	@if [ "${PIPBIN}" = "" ];then\
		echo "pip is not installed. Please install using instructions from:";\
		echo "https://pip.pypa.io/en/stable/installing/";\
		${PYTHON} -m webbrowser "https://pip.pypa.io/en/stable/installing/";\
		exit 1;\
	fi

mongod_check:
	@echo "Checking that mongod is on the path"
	@if [ "${MONGODBBIN}" = "" ];then\
	    echo "'mongod' is not on the path [MONGODBBIN is '' in the Makefile]";\
	    exit 1;\
	else\
	    echo "found mongod in ${MONGODBBIN}";\
	fi

pip_reqs: pip_check virtualenv
	@echo "Installing required python tools and packages"
	@. venv/bin/activate && pip install -r requirements.txt

virtualenv: pip_check
	pip install virtualenv
	@if [ ! -d "venv" ];then\
		echo "making virtualenv in 'venv'";\
		virtualenv -p python3 venv;\
	fi

#mtools dir and virtualenv
clean: stop_server
	rm -rf data venv req_installed

version_check:
	${PYTHON} version_check.py 3

killer:
	. venv/bin/activate && python kill_primary.py

notxns:
	. venv/bin/activate && python transaction_main.py

usetxns:
	@. venv/bin/activate && python transaction_main.py --usetxns

watch_seats:
	@. venv/bin/activate && python watch_transactions.py --collection seats

watch_payments:
	@. venv/bin/activate && python watch_transactions.py --collection payments

download:
	@echo "You can download the latest version of MongoDB from https://www.mongodb.com/download-center?jmp=nav#production"
	@python -m webbrowser "https://www.mongodb.com/download-center#production"
