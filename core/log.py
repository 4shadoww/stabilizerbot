import datetime
import sys
from core import path
from core.config_loader import current_config
import json

log_time = datetime.datetime.now()
log_logfilename = str(log_time)
if current_config["core"]["enable_log"]:
	logfile = open(path.main()+"logs/"+log_logfilename+".log", "a")

if current_config["core"]["log_warnings"]:
	warfile = open(path.main()+"logs/warnings.log", "a")

def printlog(*message, end="\n"):
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "

	log_time = datetime.datetime.now()
	line = str(log_time)+" "+finalmessage+end
	if current_config["core"]["enable_log"]:
		logfile.write(line)
	sys.stdout.write(line)

def log(*message, end="\n"):
	finalmessage = ""
	for l, mes in enumerate(message):
		finalmessage += str(mes)
		if l != len(message):
			finalmessage += " "

	if current_config["core"]["enable_log"]:
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
	crashfile = open(path.main()+"logs/crashreport.log", "a")
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

def logdecision(title, revid, user, timestamp, scores):
	decfile = open(path.main()+"logs/decision.log", "a")
	finalmessage = "{\"title\": "+"\""+title+"\", "+"\"revid\": "+str(revid)+", "+"\"user\": "+"\""+user+"\", "+"\"timestamp\": "+"\""+str(timestamp)+"\", "+"\"scores\": "+json.dumps(scores)+"}"

	decfile.flush()
	decfile.write(finalmessage+"\n")
	decfile.close()

def statusreport(*message):
	if current_config["core"]["status_log"]:
		statusfile = open(path.main()+"logs/status", "w")
		finalmessage = ""
		for l, mes in enumerate(message):
			finalmessage += str(mes)
			if l != len(message):
				finalmessage += " "

		time = datetime.datetime.now()
		line = str(time)+" "+finalmessage+"\n"
		statusfile.write(line)
		statusfile.close()
def usagereport(*message):
	if current_config["core"]["usage_log"]:
		usagefile = open(path.main()+"logs/usage.txt", "a")

		finalmessage = ""
		for l, mes in enumerate(message):
			finalmessage += str(mes)
			if l != len(message):
				finalmessage += " "

		time = datetime.datetime.now()
		line = str(time)+" "+finalmessage+"\n"
		usagefile.flush()
		usagefile.write(line)
		usagefile.close()
