# Import python modules
import datetime

# Import pywikibot
from pywikibot.site import APISite
import pywikibot

site = pywikibot.Site()
#TODO: Rewrite completely
# Get reverts from article
# Used with tumple that createEditList returns
def getRevertList(edits, inf = False, end_hours = 0, end_minutes = 0, end_seconds = 0):
	reverts = []

	end = datetime.timedelta(hours=end_hours, minutes=end_minutes, seconds=end_seconds)

	timeutc = datetime.datetime.utcnow()

	for i in range(len(edits)):
		if edits[i]["timestamp"] < timeutc-end and not inf:
			break

		for x in range(i+1, len(edits)):
			if edits[i]["text"] == edits[x]["text"]:
				revert = {"reverter": edits[i]["user"], "victim": edits[x]["user"], "revid": edits[i]["revid"], "oldrevid": edits[x]["revid"]}
				reverts.append(revert)
				break
	return reverts

# Create edit history from article
def createEditList(title, inf = False, end_hours = 0, end_minutes = 0, end_seconds = 0):
	edits = []

	end = datetime.timedelta(hours=end_hours, minutes=end_minutes, seconds=end_seconds)
	timeutc = datetime.datetime.utcnow()

	page = pywikibot.Page(site, title)

	for rev in page.getVersionHistory():
		if rev[1] < timeutc-end and not inf:
			break
		edit =  {"title": title, "text": page.getOldVersion(rev[0]), "user": rev[2], "revid": rev[0], "timestamp": rev[1]}
		edits.append(edit)

	return edits
