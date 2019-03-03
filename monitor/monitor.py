#!/usr/bin/python3
import argparse
from jinja2 import Environment, FileSystemLoader
import datetime
import time
import db.mongodb as md
import re
from utils.email_obj import EmailObj
from setup import *


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Daily Report')
    # parser.add_argument('-i', help='Instance')
    # parser.add_argument('-d', help='Included Days')
    parser.add_argument('-f', help='Log file name')
    parser.add_argument('-r', help='Receiver Email Address')

    args = parser.parse_args()
    # print(args)
    if not (args.r and args.f):
        parser.print_help()
        exit(1)

    # instance_id = args.i
    # days = args.d
    email_addr = args.r
    file_name = args.f

    # template_dir = location('monitor/template')
    # print(template_dir)
    subject = 'Quant Alert'

    modified_time = datetime.datetime.fromtimestamp(os.stat(file_name).st_mtime)

    if datetime.datetime.now() < modified_time + datetime.timedelta(minutes=10):
        print("Everything is okey")
        exit(0)
        # construct html
    # env = Environment(
    #     loader=FileSystemLoader(template_dir),
    # )
    # template = env.get_template('alert.html')
    # html = template.render(orders=orders, process_info=process_info)
    html = "Quant is dead. Please check"
    print(html)
    email_obj = EmailObj(email_srv, email_user, email_pwd, email_port)
    email_obj.send_mail(subject, html, email_user, to_addr=email_addr)

