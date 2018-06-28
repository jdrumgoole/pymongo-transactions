#!/usr/bin/env bash

MONGOD_BINDIR=./mongodb-osx-x86_64-4.0.0/bin
PATH=${MONGOD_BINDIR}:${PATH}

if [ "$1" == "stop" ];then
    echo "Stopping replica set"
    mlaunch stop
elif [ -d "$MONGOD_BINDIR" ]; then
  if [ -d "data/txntest" ]; then
    echo "Starting replica set"
    mlaunch start
  else
  echo "Initalising replica set"
    mlaunch init --port 27100 --replicaset --name "txntest"
  fi

fi
