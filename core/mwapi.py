# Import python modules
import json
from urllib.request import urlopen

# Import pywikibot
from pywikibot.comms import http as api_req

# Import core modules
from core import config_loader

def parameterMaker(base, values):
	final_str = base
	for i in range(len(values)):
		final_str += str(values[i])

		if i < len(values) - 1:
			final_str += "|"

	return final_str

class ORES:
	base_url = "https://ores.wikimedia.org/scores/"+config_loader.core_config["lang"]+"wiki"
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
		base_url = "https://"+config_loader.core_config["lang"]+".wikipedia.org/w/api.php?action=query&prop=revisions"
		parameters = parameterMaker("&revids=", revids)+parameterMaker("&rvprop=", param)+"&format=json"
		final = str(base_url+parameters).replace(" ", "%20")

		return json.loads(api_req.fetch(final).content)

	def getAbuseFiler(self, user, timestamp, filters, param=["ids", "user", "title", "action", "result", "timestamp", "hidden", "revid"]):
		base_url = "https://"+config_loader.core_config["lang"]+".wikipedia.org/w/api.php?action=query&list=abuselog"
		parameters = parameterMaker("&aflfilter=", filters)+parameterMaker("&aflprop=", param)+"&afluser="+user+"&afldir=newer"+"&aflstart="+timestamp+"&format=json"
		final = str(base_url+parameters).replace(" ", "%20")

		return json.loads(api_req.fetch(final).content)
