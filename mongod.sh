#!/usr/bin/env bash

MONGOD_BINDIR=./mongodb-osx-x86_64-4.0.0-rc4/bin
PATH=${MONGOD_BINDIR}:${PATH}

if [ "$1" == "stop" ];then
    echo "Stopping replica set"
    mlaunch stop
elif [ "$1" == "chaos" ];then
    echo "Starting replica set"
    mlaunch start
    while true ; do
        mlaunch kill primary
        sleep 0.5
        mlaunch start
    done
elif [ -d "$MONGOD_BINDIR" ]; then
  if [ -d "data/txntest" ]; then
    echo "Starting replica set"
    mlaunch start
  else
  echo "Initalising replica set"
    mlaunch init --port 27100 --replicaset --name "txntest"
  fi

fi
