# Import pywikibot
from pywikibot.site import APISite
import pywikibot

# Import core modules
from core import data_holders

site = pywikibot.Site()

def getRevertCount(edits, older=None):
	reverts = 0

	for i in range(len(edits)):
		for x in range(i+1, len(edits)):
			if edits[i].text == edits[x].text:
				reverts += 1
				break
	return reverts

def createEditList(page):
	edits = []

	page = pywikibot.Page(site, page)

	for rev in page.getVersionHistory():
		edit = data_holders.Edit(page.getOldVersion(rev[0]), rev[2], rev[0], rev[1])
		edits.append(edit)

	return edits
