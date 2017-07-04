# Import python modules
import datetime

from core import timelib
from core import yapi

api = yapi.MWAPI

# Get reverts from article
def getReverts(title, hours=1):
	reverts = []

	end = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
	edits = api.getPageHistory(title, rvprop="timestamp|user|content|ids", rvend=timelib.toString(end))
	for i in range(len(edits)):
		for x in range(i+1, len(edits)):
			if edits[i]["*"] == edits[x]["*"]:
				revert = {"reverter": edits[i]["user"], "victim": edits[i+1]["user"], "revid": edits[i]["revid"], "oldrevid": edits[i+1]["revid"]}
				reverts.append(revert)
				break
	return reverts
