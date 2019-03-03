#!/usr/bin/python
import os

location = lambda x: os.path.join(
    os.path.dirname(os.path.realpath(__file__)), x)

#db_name = location('database/main.db')
db_name = 'binance'
mongo_user = os.environ.get('MONGO_USER')
mongo_pwd = os.environ.get('MONGO_PWD')
db_url = "mongodb://localhost:27017/"

email_srv = os.environ.get('EMAIL_SMTP')
email_user = os.environ.get('EMAIL_FROM')
email_pwd = os.environ.get('EMAIL_PWD')
email_port = os.environ.get('EMAIL_PORT')
