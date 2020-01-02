#!/usr/bin/env bash
docker run --rm -d --network host --name mongo1 mongo:4.0.0 --replSet txntest --port 27100
docker run --rm -d --network host --name mongo2 mongo:4.0.0 --replSet txntest --port 27101
docker run --rm -d --network host --name mongo3 mongo:4.0.0 --replSet txntest --port 27102
sleep 3
docker exec -it mongo1 mongo --port 27100 --eval \
'rs.initiate({
  _id: "txntest",
  members: [
    { _id: 0, host: "localhost:27100" },
    { _id: 1, host: "localhost:27101" },
    { _id: 2, host: "localhost:27102" }]});'
