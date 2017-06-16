## TODO: Make this code cleaner
## TODO:

# Import python modules
import json
from urllib.request import urlopen
from urllib.parse import urlencode
import traceback

# Import pywikibot
from pywikibot.comms import http as api_req
from pywikibot.data import api
import pywikibot

# Import core modules
from core import config_loader
from core.log import *

site = pywikibot.Site()
site.login()

def parameterMaker(base, values):
	final_str = base
	for i in range(len(values)):
		final_str += str(values[i])

		if i < len(values) - 1:
			final_str += "|"

	return final_str

class ORES:
	base_url = "https://ores.wikimedia.org/scores/"+config_loader.current_config["core"]["lang"]+"wiki"
	revids_url = "?revids="
	models_url = "&models="

	def getScore(self, revids, models=["reverted", "goodfaith", "damaging"]):
		request_url = self.base_url+parameterMaker(self.revids_url, revids)+parameterMaker(self.models_url, models)
		request = urlopen(request_url)
		try:
			request = request.read().decode('utf8')
		except AttributeError:
			pass
		return json.loads(request)

class MWAPI:

	def getRevision(self, revids, param=["ids", "timestamp", "flags", "user"]):
		base_url = "https://"+config_loader.current_config["core"]["lang"]+".wikipedia.org/w/api.php?action=query&prop=revisions"
		parameters = parameterMaker("&revids=", revids)+parameterMaker("&rvprop=", param)+"&format=json"
		final = str(base_url+parameters).replace(" ", "%20")

		return json.loads(api_req.fetch(final).content)

	def getAbuseFiler(self, user, timestamp, filters, param=["ids", "user", "title", "action", "result", "timestamp", "hidden", "revid"]):
		base_url = "https://"+config_loader.current_config["core"]["lang"]+".wikipedia.org/w/api.php?action=query&list=abuselog"
		parameters = parameterMaker("&aflfilter=", filters)+parameterMaker("&aflprop=", param)+"&afluser="+user+"&afldir=newer"+"&aflstart="+timestamp+"&format=json"
		final = str(base_url+parameters).replace(" ", "%20")

		return json.loads(api_req.fetch(final).content)

	def stabilized(self, title):
		final = "https://"+config_loader.current_config["core"]["lang"]+".wikipedia.org/w/api.php?action=query&prop=flagged&titles="+title+"&format=json"
		final = final.replace(" ", "%20")

		query = json.loads(api_req.fetch(final).content)
		answer = query["query"]["pages"]
		
		for pageid in answer:
			if "flagged" not in answer[pageid]:
				return False
			elif "protection_level" in answer[pageid]["flagged"]:
				return True
			else:
				return False

		return False

	def reviewed(self, title):
		final = "https://"+config_loader.current_config["core"]["lang"]+".wikipedia.org/w/api.php?action=query&prop=info|flagged&titles="+title+"&format=json"
		final = final.replace(" ", "%20")

		query = json.loads(api_req.fetch(final).content)
		answer = query["query"]["pages"]

		for pageid in answer:
			if "flagged" in answer[pageid]:
				return True
			else:
				return False

		return False

	def stabilize(self, title, reason, expiry="infinite"):
		edittoken = site.tokens['edit']

		try:
			req = api.Request(site=site, action="stabilize", title=title, reason=reason, default="stable", expiry=expiry, token=edittoken)
			req.submit()
		except:
			printlog("error: failed to stabilize check crasreport for details")
			print(traceback.format_exc())
			crashreport(traceback.format_exc())
			return False

		return True
