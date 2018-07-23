#!/usr/bin/env bash
docker run --rm --network host pymongo-transactions/python:1.0 watch_transactions.py --collection payments $@
