#!/usr/bin/env python3

# Import python modules
import sys

# Import path tool
from core import path

# Append lib path
sys.path.append(path.main()+"core/lib/")

# Set pywikibot config path
os.environ["PYWIKIBOT2_DIR"] = path.main()

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
