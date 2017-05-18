# Import python modules
import datetime
import time

# Import pywikibot
from pywikibot.site import APISite
import pywikibot

# Import core modules
from core import data_holders

site = pywikibot.Site()

def getRevertList(edits, older=datetime.timedelta(hours=40, minutes=0, seconds=0)):
	reverts = []
	timeutc = datetime.datetime.utcnow()

	for i in range(len(edits)):
		if edits[i].timestamp < timeutc-older:
			print("too old")
			break

		for x in range(i+1, len(edits)):
			if edits[i].text == edits[x].text:
				revert = {"reverter": edits[i].user, "victim": edits[x].user, "revid": edits[i].revid, "oldrevid": edits[x].revid}
				reverts.append(revert)
				break
	return reverts

def createEditList(page):
	edits = []

	page = pywikibot.Page(site, page)

	for rev in page.getVersionHistory():
		edit = data_holders.Edit(page.title(), page.getOldVersion(rev[0]), rev[2], rev[0], rev[1])
		edits.append(edit)

	return edits
