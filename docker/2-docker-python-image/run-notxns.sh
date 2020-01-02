#!/usr/bin/env bash
docker run --rm --network host pymongo-transactions/python:1.0 transaction_main.py $@
