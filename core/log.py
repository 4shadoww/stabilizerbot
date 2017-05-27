import datetime
from core import colors
import sys
from core import config_loader

log_time = datetime.datetime.now()
log_logfilename = str(log_time)
if config_loader.core_config["enable_log"]:
	logfile = open("core/logs/"+log_logfilename+".log", "a")

if config_loader.core_config["log_warnings"]:
	warfile = open("core/logs/warnings.log", "a")

def printlog(*message, end="\n"):
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "

	log_time = datetime.datetime.now()
	line = str(log_time)+" "+finalmessage+end
	if config_loader.core_config["enable_log"]:
		logfile.write(line)
	sys.stdout.write(line)

def log(*message, end="\n"):
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "

	if config_loader.core_config["enable_log"]:
		log_time = datetime.datetime.now()
		line = str(log_time)+" "+finalmessage+end
		logfile.write(line)


def debug(*message, end="\n"):
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "

	sys.stdout.write(finalmessage+end)
	log(finalmessage)

def crashreport(*message):
	crashfile = open("core/logs/crashreport.log", "a")
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "
	time = datetime.datetime.now()
	line = str(time)+" "+finalmessage+"\n"
	crashfile.flush()
	crashfile.write(line)
	crashfile.close()

def logdecision(*message):
	decfile = open("core/logs/decision.log", "a")
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "
	decfile.flush()
	decfile.write(finalmessage)
	decfile.close()
