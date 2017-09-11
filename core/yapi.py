# Import python modules
import json
from urllib.request import urlopen
from urllib.parse import urlencode
import traceback
import logging

from core.session import session

# Import core modules
from core.config_loader import cur_conf

logger = logging.getLogger("infolog")

def parameterMaker(values):
	if type(values) != list:
		return values

	final_str = ""
	for i in range(len(values)):
		final_str += str(values[i])

		if i < len(values) - 1:
			final_str += "|"

	return final_str

class ORES:
	base_url = "https://ores.wikimedia.org/scores/"+cur_conf["core"]["lang"]+"wiki?"

	def getScore(revids, models=["reverted", "goodfaith", "damaging"]):
		params = {
			"revids": parameterMaker(revids),
			"models": parameterMaker(models)
		}

		request_url = ORES.base_url + urlencode(params)

		request = urlopen(request_url)
		try:
			request = request.read().decode('utf8')
			return json.loads(request)
		except AttributeError:
			return False
class MWAPI:
	def getRevision(revids, param=["ids", "timestamp", "flags", "user"]):
		params = {
			"action": "query",
			"prop": "revisions",
			"revids": parameterMaker(revids),
			"rvprop": parameterMaker(param),
			"format": "json"
		}

		return session.get(params)

	def getAbuseFiler(user, timestamp, filters, param=["ids", "user", "title", "action", "result", "timestamp", "hidden", "revid"]):
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

		return session.get(params)

	def stabilized(title):
		params = {
			"action": "query",
			"prop": "flagged",
			"titles": title,
			"format": "json"
		}


		query = session.get(params)
		answer = query["query"]["pages"]

		for pageid in answer:
			if "flagged" in answer[pageid] and "protection_level" in answer[pageid]["flagged"]:
				return True
			else:
				return False

		return False

	def reviewed(title):
		params = {
			"action": "query",
			"prop": "flagged",
			"titles": title,
			"format": "json"
		}
		query = session.get(params)
		answer = query["query"]["pages"]

		for pageid in answer:
			if ("flagged" in answer[pageid] and "stable_revid" in answer[pageid]["flagged"]
			and answer[pageid]["flagged"]["stable_revid"] != "" and answer[pageid]["flagged"]["stable_revid"] != None
			and type(answer[pageid]["flagged"]["stable_revid"]) is int):
				return True

			return False

		return False

	def getToken(token_type):
		params = {
			"action": "query",
			"meta": "tokens",
			"type": parameterMaker(token_type)
		}
		return session.get(params)["query"]["tokens"]

	def stabilize(title, reason, expiry="infinite"):
		params = {
			"action": "stabilize",
			"title": title,
			"reason": reason,
			"default": "stable",
			"expiry": expiry,
			"token": MWAPI.getToken(["csrf"])["csrftoken"]
		}

		try:
			session.post(params)
		except:
			logger.error("failed to stabilize check crasreport for details")
			logger.critical(traceback.format_exc())
			return False

		return True

	def getLatestRev(title):
		params = {
			"action": "query",
			"prop": "revisions",
			"titles": title,
			"rvprop": "ids"
		}
		query = session.get(params)["query"]["pages"]

		for pageid in query:
			if pageid == "-1":
				return False
			if "revisions" not in query[pageid]:
				return False
			return query[pageid]["revisions"][0]["revid"]

		return False

	def getSha1(revid):
		params = {
			"action": "query",
			"prop": "revisions",
			"revids": revid,
			"rvprop": "sha1",
			"format": "json"
		}
		query = session.get(params)["query"]["pages"]

		for pageid in query:
			if pageid == "-1":
				return False
			if "revisions" not in query[pageid]:
				return False
			return query[pageid]["revisions"][0]["sha1"]

		return False

	def getText(title):
		params = {
			"action": "query",
			"prop": "revisions",
			"titles": title,
			"rvprop": "content"
		}
		query = session.get(params)["query"]["pages"]
		for pageid in query:
			if pageid == "-1":
				return False
			if "revisions" not in query[pageid]:
				return False
			return query[pageid]["revisions"][0]["*"]

		return False

	def getTextById(revid):
		params = {
			"action": "query",
			"prop": "revisions",
			"revids": revid,
			"rvprop": "content"
		}
		query = session.get(params)["query"]["pages"]
		for pageid in query:
			if pageid == "-1":
				return False
			if "revisions" not in query[pageid]:
				return False
			return query[pageid]["revisions"][0]["*"]

		return False

	def getPageHistory(title, **kwargs):
		params = {
			"action": "query",
			"prop": "revisions",
			"titles": title,
			"rvprop": "ids|timestamp|flags|comment|user"
		}
		for key, val in kwargs.items():
			params[key] = val

		query = session.get(params)["query"]["pages"]

		for pageid in query:
			if pageid == "-1":
				return False
			if "revisions" not in query[pageid]:
				return False
			return query[pageid]["revisions"]

		return False

	def getUserRights(user):
		params = {
			"action": "query",
			"list": "users",
			"ususers": user,
			"usprop": "groups"
		}
		query = session.get(params)

		if "groups" in query["query"]["users"][0]:
			return query["query"]["users"][0]["groups"]

		return False

	def isReverted(title, revid):
		pick = False

		revisions = MWAPI.getPageHistory(title, rvprop="ids", rvlimit=10)
		for rev in revisions:
			if rev["revid"] == revid:
				return False
			sha10 = MWAPI.getSha1(rev["revid"])
			if not sha10:
				continue

			for drev in revisions:
				if drev["revid"] == revid:
					pick = True
					continue
				if not pick:
					continue
				sha11 = MWAPI.getSha1(rev["revid"])

				if sha10 == sha11:
					return True

			pick = False

		return False
