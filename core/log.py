import datetime
from core import config
from core import colors
import sys

log_time = datetime.datetime.now()
log_logfilename = str(log_time)
if config.enable_log:
	logfile = open('core/log/'+log_logfilename+'.log', 'a')

if config.log_warnings:
	warfile = open('core/log/warnings.log', 'a')

def printlog(*message, end='\n'):
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "

	log_time = datetime.datetime.now()
	line = str(log_time)+' '+finalmessage+end
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
		log_time = datetime.datetime.now()
		line = str(log_time)+' '+finalmessage+end
		logfile.write(line)


def debug(*message, end='\n'):
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "

	sys.stdout.write(finalmessage+end)
	log(finalmessage)
	
def crashreport(*message):
	crashfile = open('core/log/crashreport.log', 'a')
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "
	time = datetime.datetime.now()
	line = str(time)+' '+finalmessage+"\n"
	crashfile.flush()
	crashfile.write(line)
