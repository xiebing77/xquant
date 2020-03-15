#!/usr/bin/python
"""xquant log"""

import logging
import logging.handlers

logger = logging.getLogger('QuantLogger')
logger.setLevel(logging.DEBUG)

def init(logname):
    global logger
    logging.basicConfig(level=logging.NOTSET, filename=logname)
    extra = {'tags':logname}
    handler = logging.handlers.SysLogHandler(address = ('127.0.0.1', 1514))
    f = logging.Formatter('%(tags)s: %(message)s')
    handler.setFormatter(f)
    logger.addHandler(handler)
    logger = logging.LoggerAdapter(logger, extra)

def info(info):
    logger.info(info)

def warning(info):
    logger.warning(info)

def error(info):
    logger.error(info)

def critical(info):
    logger.critical(info)

def debug(info):
    logger.debug(info)
