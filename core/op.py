# Import python modules
import datetime
import time

# Import pywikibot
from pywikibot.site import APISite
import pywikibot

# Import core modules
from core import data_holders

site = pywikibot.Site()

def getRevertList(edits, inf = False, older_hours = 40, older_minutes = 0, older_seconds = 0):
	reverts = []

	older = datetime.timedelta(hours=older_hours, minutes=older_minutes, seconds=older_seconds)

	timeutc = datetime.datetime.utcnow()

	for i in range(len(edits)):
		if edits[i].timestamp < timeutc-older and not inf:
			break

		for x in range(i+1, len(edits)):
			if edits[i].text == edits[x].text:
				revert = {"reverter": edits[i].user, "victim": edits[x].user, "revid": edits[i].revid, "oldrevid": edits[x].revid}
				reverts.append(revert)
				break
	return reverts

def createEditList(title, inf = False, older_hours = 40, older_minutes = 0, older_seconds = 0):
	edits = []

	older = datetime.timedelta(hours=older_hours, minutes=older_minutes, seconds=older_seconds)
	timeutc = datetime.datetime.utcnow()

	page = pywikibot.Page(site, title)

	for rev in page.getVersionHistory():
		if rev[1] < timeutc-older and not inf:
			break
		edit = data_holders.Edit(title, page.getOldVersion(rev[0]), rev[2], rev[0], rev[1])
		edits.append(edit)

	return edits
