#!/usr/bin/python
"""xquant log"""

import logging


def init(logfilename):
    logging.basicConfig(level=logging.NOTSET, filename=logfilename)


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

