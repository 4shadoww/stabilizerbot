# Import python modules
import json
from urllib.request import urlopen

# Import pywikibot
from pywikibot.comms import http as api_req

# Import core modules
import core.config

def parameterMaker(base, values):
	final_str = base
	for i in range(len(values)):
		final_str += str(values[i])

		if i < len(values) - 1:
			final_str += "|"

	return final_str

class ORES:
	base_url = "https://ores.wikimedia.org/scores/"+core.config.lang+"wiki"
	revids_url = "?revids="
	models_url = "&models="


	def getScore(self, revids, models=["reverted", "goodfaith", "damaging"]):
		request_url = self.base_url+parameterMaker(self.revids_url, revids)+parameterMaker(self.models_url, models)

		return json.load(urlopen(request_url))

class MWAPI:

	def getRevision(self, revids, param=["ids", "timestamp", "flags", "user"]):
		base_url = "https://"+core.config.lang+".wikipedia.org/w/api.php?action=query&prop=revisions"
		parameters = parameterMaker("&revids=", revids)+parameterMaker("&rvprop=", param)+"&format=json"
		final = base_url+parameters

		return json.loads(api_req.fetch(final).content)
