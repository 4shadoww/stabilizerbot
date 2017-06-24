import optparse
import os
from core import path

def main():
	parser = optparse.OptionParser()

	parser.add_option('-n', '--name',
		action="store", dest="name",
		help="grid job name", default=None)

	options, args = parser.parse_args()

	if options.name:
		command = "jstart -mem 500m -N " + options.name + " " + path.main() + "grid.sh"
		os.system(command)
	else:
		parser.print_help()
if __name__ == "__main__":
	main()
