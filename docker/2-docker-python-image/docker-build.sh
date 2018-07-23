#!/usr/bin/env bash
cd ../..
docker build --no-cache -f docker/2-docker-python-image/Dockerfile -t pymongo-transactions/python:1.0 .
