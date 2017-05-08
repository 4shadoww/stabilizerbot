#!/usr/bin/env python3

# Import python modules
import sys

# Append lib path
sys.path.append("core/lib/")

# Import core modules
from core import worker

def main():
	try:
		wr = worker.Worker()
		wr.run()
	except KeyboardInterrupt:
		print("terminating yuno...")

if __name__ == "__main__":
	main()
