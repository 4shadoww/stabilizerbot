# Import python modules
import json

# Import pywikibot
import pywikibot

# Import core modules
import core.config
from core.log import *

has_config = False
online_config = None
last_config_version = 0
site = pywikibot.Site()
page = pywikibot.Page(site, core.config.online_conf_path)

def checkForUpdate():
	global last_config_version
	global online_config
	global has_config

	if not page.exists():
		printlog("error: config page \""+core.config.online_conf_path+"\" doesn't exists")
		return 1
	if not last_config_version or page.latestRevision() != last_config_version:
		last_config_version = page.latestRevision()
		online_config = json.loads(page.text)
		has_config = True
