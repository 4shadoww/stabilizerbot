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

def parameterMaker(values):
	final_str = ""
	for i in range(len(values)):
		final_str += str(values[i])

		if i < len(values) - 1:
			final_str += "|"

	return final_str

class ORES:
	base_url = "https://ores.wikimedia.org/scores/"+config_loader.current_config["core"]["lang"]+"wiki?"

	def getScore(self, revids, models=["reverted", "goodfaith", "damaging"]):
		params = {
			"revids": parameterMaker(revids),
			"models": parameterMaker(models)
		}

		request_url = self.base_url + urlencode(params)

		request = urlopen(request_url)
		try:
			request = request.read().decode('utf8')
			return json.loads(request)
		except AttributeError:
			return False
class MWAPI:
	base_url = "https://"+config_loader.current_config["core"]["lang"]+".wikipedia.org/w/api.php?"

	def getRevision(self, revids, param=["ids", "timestamp", "flags", "user"]):
		params = {
			"action": "query",
			"prop": "revisions",
			"revids": parameterMaker(revids),
			"rvprop": parameterMaker(param),
			"format": "json"
		}

		final = self.base_url + urlencode(params)

		return json.loads(api_req.fetch(final).content)

	def getAbuseFiler(self, user, timestamp, filters, param=["ids", "user", "title", "action", "result", "timestamp", "hidden", "revid"]):
		params = {
			"action": "query",
			"list": "abuselog",
			"aflfilter": parameterMaker(filters),
			"aflprop": parameterMaker(param),
			"afluser": user,
			"afldir": "newer",
			"aflstart": timestamp,
			"format": "json"
		}

		final = self.base_url + urlencode(params)

		return json.loads(api_req.fetch(final).content)

	def stabilized(self, title):
		params = {
			"action": "query",
			"prop": "flagged",
			"titles": title,
			"format": "json"
		}

		final = self.base_url + urlencode(params)

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
		params = {
			"action": "query",
			"prop": "flagged",
			"titles": title,
			"format": "json"
		}

		final = self.base_url + urlencode(params)

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
