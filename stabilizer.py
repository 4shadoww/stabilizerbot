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
from core import worker

def setupLogging():
	# Logging
	logger = logging.getLogger("infolog")
	logger.setLevel(logging.DEBUG)
	# Formatter
	formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
	# Stream
	ch = logging.StreamHandler()
	ch.setFormatter(formatter)
	ch.setLevel(logging.DEBUG)
	# Info log
	il = logging.FileHandler(path.main()+"logs/info.log")
	il.setLevel(logging.INFO)
	il.setFormatter(formatter)
	# Error log
	#el = logging.FileHandler(path.main()+"logs/crashreport.log")
	#el.setLevel(logging.ERROR)
	#el.setFormatter(formatter)
	# Add handlers
	logger.addHandler(ch)
	logger.addHandler(il)
	#logger.addHandler(el)

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

		# Start worker
		wr = worker.Worker()
		wr.run()
	except KeyboardInterrupt:
		print("terminating stabilizer...")

if __name__ == "__main__":
	main()
