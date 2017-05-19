import datetime
from core import config
from core import colors
import sys

time = datetime.datetime.now()
logfilename = str(time)
if config.enable_log:
	logfile = open('core/log/'+logfilename+'.log', 'a')

if config.log_warnings:
	warfile = open('core/log/warnings.log', 'a')

def printlog(*message, end='\n'):
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "

	time = datetime.datetime.now()
	line = str(time)+' '+finalmessage+end
	if config.enable_log == True:
		logfile.write(line)
	sys.stdout.write(line)

def log(*message, end='\n'):
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "

	if config.enable_log == True:
		time = datetime.datetime.now()
		line = str(time)+' '+finalmessage+end
		logfile.write(line)

warnings = []

def warning(*message):
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "
	warnings.append(finalmessage)

def printwarnings():
	global warnings
	for war in warnings:
		sys.stdout.write(colors.red+"warning: "+war+colors.end+"\n")
		log(war)
	del warnings[:]

def debug(*message, end='\n'):
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "

	sys.stdout.write(finalmessage+end)
	log(finalmessage)
def addwarpage(page):
	if config.log_warnings:
		warfile.flush()
		warfile.write(page+"\n")
