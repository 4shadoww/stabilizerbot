#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Import python modules
import os
import sys

# Import path tool
from core import path

# Set pywikibot config path
os.environ["PYWIKIBOT2_DIR"] = path.main()

# Append lib path
sys.path.append(path.main()+"core/lib/")

# Import core modules
from core import worker

def main():
	try:
		wr = worker.Worker()
		wr.run()
	except KeyboardInterrupt:
		print("terminating stabilizer...")
		sys.exit(1)

if __name__ == "__main__":
	main()
