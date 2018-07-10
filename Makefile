install:
	sh setup.sh

clean:
	rm -rf data venv mongodb-osx-x86_64-4.0.0 mongodb-osx-ssl-x86_64-4.0.0.tgz

start:
	sh mongod.sh start

stop:
	sh mongod.sh stop

killer:
	python kill_primary.py

watch_seats:
	python watch_transactions.py --collection seats

watch_payments:
	python watch_transactions.py --collection payments