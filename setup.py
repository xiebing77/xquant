#!/usr/bin/python
import os

location = lambda x: os.path.join(
    os.path.dirname(os.path.realpath(__file__)), x)

db_name = location('database/main.db')
mongo_user = os.environ.get('MONGO_USER')
mongo_pwd = os.environ.get('MONGO_PWD')
db_url = "mongodb://localhost:27017/"
