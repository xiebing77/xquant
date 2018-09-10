#!/usr/bin/python3
import argparse
from jinja2 import Environment, FileSystemLoader
import datetime
import db.mongodb as md
import re
from utils.email_obj import EmailObj
from setup import *


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Daily Report')
    parser.add_argument('-i', help='Instance')
    parser.add_argument('-d', help='Included Days')
    parser.add_argument('-r', help='Receiver Email Address')

    args = parser.parse_args()
    # print(args)
    if not (args.i and args.d and args.r):
        parser.print_help()
        exit(1)

    instance_id = args.i
    days = args.d
    email_addr = args.r

    template_dir = location('monitor/template')
    print(template_dir)
    subject = 'Quant Daily Report'

    process = os.popen('ps aux | grep %s | grep instance_id | grep -v grep' % instance_id).read()
    ret = re.search('python', process)
    if ret is None:
        process_info = 'Error: Instance (%s) is dead. Please check it ASAP' % instance_id
    else:
        process_info = process[ret.span()[0]:]
    print(process_info)

    db = md.MongoDB(mongo_user, mongo_pwd, db_name, db_url)
    collection = 'orders'

    begin_time = datetime.datetime.now() - datetime.timedelta(days=int(days))

    orders = db.find_sort(collection, {"instance_id": instance_id,
                                       "create_time": {"$gte": int(begin_time.timestamp())}}, 'create_time', -1)

    print('orders:', orders)
    for order in orders:
        del order['_id']
        del order['instance_id']
        order['create_time'] = datetime.datetime.fromtimestamp(order['create_time']).strftime("%Y-%m-%d %H:%M:%S")

    # construct html
    env = Environment(
        loader=FileSystemLoader(template_dir),
    )
    template = env.get_template('template.html')
    html = template.render(orders=orders, process_info=process_info)
    # print(html)
    email_obj = EmailObj(email_srv, email_user, email_pwd)
    email_obj.send_mail(subject, html, email_user, to_addr=email_addr)
