#!/usr/bin/python
"""xquant log"""

import os
import logging


def init(path, logfilename):
    #logpath = os.path.join(os.getcwd(), "log")
    logpath = os.path.join("log")
    if not os.path.exists(logpath):
        os.mkdir(logpath)

    fullpath = os.path.join(logpath, path)
    if not os.path.exists(fullpath):
        os.mkdir(fullpath)

    filename = os.path.join(fullpath, logfilename)
    logging.basicConfig(level=logging.NOTSET, filename=filename)


def info(info):
    logging.info(info)

def warning(info):
    logging.warning(info)

def error(info):
    logging.error(info)

def critical(info):
    logging.critical(info)

def debug(info):
    logging.debug(info)

