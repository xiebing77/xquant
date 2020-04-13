#!/usr/bin/python
import os

location = lambda x: os.path.join(
    os.path.dirname(os.path.realpath(__file__)), x)

#db_name = location('database/main.db')
db_order_name = "xquant"
mongo_user = os.environ.get('MONGO_USER')
mongo_pwd = os.environ.get('MONGO_PWD')
mongo_port = os.environ.get('MONGO_PORT')
mongo_port = '%s' % (mongo_port) if mongo_port else '27017'
db_url = "mongodb://localhost:%s/" % (mongo_port)

email_srv = os.environ.get('EMAIL_SMTP')
email_user = os.environ.get('EMAIL_FROM')
email_pwd = os.environ.get('EMAIL_PWD')
email_port = os.environ.get('EMAIL_PORT')
