import os
import sys

def main():
	return os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__)) + "/"
