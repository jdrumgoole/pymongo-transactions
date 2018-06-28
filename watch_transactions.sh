#!/usr/bin/env bash
python watch_transactions.py --host mongodb://localhost:27100/?replicaSet=txntest --watch $1