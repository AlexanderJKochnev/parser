#!/bin/bash

touch config.yaml docker-compose.yml Dockerfile requirements.txt
mkdir -p app/models app/parsers app/storage &&
cd app &&
touch __init__.py config.py gui.py main.py utils.py &&
touch models/__init__.py models/postgres.py models/mongo.py &&
touch parsers/__init__.py parsers/fetcher.py parsers/processor.py &&
touch storage/__init__.py storage/postgres.py storage/mongo.py