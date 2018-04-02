#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Import python modules
import os
import sys
import logging

# Import path tool
from core import path

# Append lib path
sys.path.append(path.main()+"core/lib/")

# Import core modules
from core import config_loader as cfgl
from core import worker
from core import session

class LessThanFilter(logging.Filter):
    def __init__(self, exclusive_maximum, name=""):
        super(LessThanFilter, self).__init__(name)
        self.max_level = exclusive_maximum

    def filter(self, record):
        return 1 if record.levelno < self.max_level else 0

def setupLogging():
    # Logging
    logger = logging.getLogger("infolog")
    logger.setLevel(logging.DEBUG)
    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    # Stream
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    ch.addFilter(LessThanFilter(logging.ERROR))
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)
    # Error stream
    eh = logging.StreamHandler(sys.stderr)
    eh.setLevel(logging.ERROR)
    eh.setFormatter(formatter)
    logger.addHandler(eh)
    # Info log
    if cfgl.cur_conf["core"]["enable_log"]:
        il = logging.FileHandler(path.main()+"logs/info.log")
        il.setLevel(logging.DEBUG)
        il.addFilter(LessThanFilter(logging.ERROR))
        il.setFormatter(formatter)
        logger.addHandler(il)
    # Error log
    el = logging.FileHandler(path.main()+"logs/crashreport.log")
    el.setLevel(logging.ERROR)
    el.setFormatter(formatter)
    logger.addHandler(el)

    # Stable logger
    slogger = logging.getLogger("stablelog")
    slogger.setLevel(logging.DEBUG)
    # Info log
    isl = logging.FileHandler(path.main()+"logs/stable.log")
    isl.setLevel(logging.INFO)
    isl.setFormatter(formatter)
    # Add handlers
    slogger.addHandler(isl)

def main():
    try:
        setupLogging()
        logger = logging.getLogger("infolog")
        # Login
        logger.info("logging...")
        session.login()

        # Start worker
        wr = worker.Worker()
        wr.run()
    except KeyboardInterrupt:
        logger.info("terminating stabilizer...")

if __name__ == "__main__":
    main()
