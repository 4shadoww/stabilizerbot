# Import python modules
import json
import requests
import traceback
import logging

from core.session import session
from user_config import access_token

# Import core modules
from core.config_loader import cur_conf

logger = logging.getLogger("infolog")

LIFTWING_BASE_URL = "https://api.wikimedia.org/service/lw/inference/v1/models/"
LIFTWING_DAMAGING_URL = LIFTWING_BASE_URL + cur_conf["core"]["lang"] + "wiki-damaging:predict"
LIFTWING_GOODFAITH_URL = LIFTWING_BASE_URL + cur_conf["core"]["lang"] + "wiki-goodfaith:predict"

def parameter_maker(values):
    if type(values) != list:
        return values

    final_str = ""
    for i in range(len(values)):
        final_str += str(values[i])

        if i < len(values) - 1:
            final_str += "|"

    return final_str


def get_score(revid):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + access_token,
        'User-Agent': 'stabilizerbot (https://wikitech.wikimedia.org/wiki/User:4shadoww)'
    }

    data = {
        "rev_id": int(revid)
    }

    try:
        damaging = requests.post(LIFTWING_DAMAGING_URL, headers=headers, data=json.dumps(data))
        goodfaith = requests.post(LIFTWING_GOODFAITH_URL, headers=headers, data=json.dumps(data))

        damaging_data = json.loads(damaging.text)[cur_conf['core']['lang']+'wiki']['scores'][str(revid)]['damaging']['score']
        goodfaith_data = json.loads(goodfaith.text)[cur_conf['core']['lang']+'wiki']['scores'][str(revid)]['goodfaith']['score']
        return {'damaging': damaging_data, 'goodfaith': goodfaith_data}
    except AttributeError:
        return False


# TODO api calls could be sent as batches
# to make responses faster and save resources on api
def get_revision(revids, param=None):
    if not param:
        param = ["ids", "timestamp", "flags", "user"]
    params = {
        "action": "query",
        "prop": "revisions",
        "revids": parameter_maker(revids),
        "rvprop": parameter_maker(param),
        "format": "json"
    }

    return session.get(params)

def get_abuse_filter(user, timestamp, filters, param=None):
    if not param:
        param = ["ids", "user", "title", "action", "result", "timestamp", "hidden", "revid"]
    params = {
        "action": "query",
        "list": "abuselog",
        "aflfilter": parameter_maker(filters),
        "aflprop": parameter_maker(param),
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

    try:
        query = session.get(params)
    except ValueError:
        return False
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
        if ("flagged" in answer[pageid] and "stable_revid" in answer[pageid]["flagged"] and
            answer[pageid]["flagged"]["stable_revid"] != "" and
            answer[pageid]["flagged"]["stable_revid"] != None and
            type(answer[pageid]["flagged"]["stable_revid"]) is int):

            return True

        return False

    return False

def latest_pending(title):
    params = {
        "action": "query",
        "prop": "flagged",
        "titles": title,
        "format": "json"
    }

    query = session.get(params)
    answer = query["query"]["pages"]

    for pageid in answer:
        if ("flagged" in answer[pageid] and "stable_revid" in answer[pageid]["flagged"] and
            "pending_since" in answer[pageid]["flagged"] and
            answer[pageid]["flagged"]["stable_revid"] != "" and
            answer[pageid]["flagged"]["stable_revid"] != None and
            type(answer[pageid]["flagged"]["stable_revid"]) is int and
            answer[pageid]["flagged"]["pending_since"] != ""):

            return True

        return False

    return False

def should_check(title):
    params = {
        "action": "query",
        "prop": "flagged",
        "titles": title,
        "format": "json"
    }

    try:
        query = session.get(params)
    except ValueError:
        return False
    answer = query["query"]["pages"]

    for pageid in answer:
        # Is stabilised
        if "flagged" in answer[pageid] and "protection_level" in answer[pageid]["flagged"]:
            return False
        # Page is not reviewed ever
        elif not ("flagged" in answer[pageid] and "stable_revid" in answer[pageid]["flagged"] and
                  answer[pageid]["flagged"]["stable_revid"] != "" and
                  answer[pageid]["flagged"]["stable_revid"] != None and
                  type(answer[pageid]["flagged"]["stable_revid"]) is int):
            return False

        # Latest is not pending
        elif not ("flagged" in answer[pageid] and "stable_revid" in answer[pageid]["flagged"] and
                  "pending_since" in answer[pageid]["flagged"] and
                  answer[pageid]["flagged"]["stable_revid"] != "" and
                  answer[pageid]["flagged"]["stable_revid"] != None and
                  type(answer[pageid]["flagged"]["stable_revid"]) is int and
                  answer[pageid]["flagged"]["pending_since"] != ""):
            return False

        return True

    return False


def get_token(token_type):
    params = {
        "action": "query",
        "meta": "tokens",
        "type": parameter_maker(token_type)
    }
    return session.get(params)["query"]["tokens"]

def stabilize(title, reason, expiry="infinite"):
    params = {
        "action": "stabilize",
        "title": title,
        "reason": reason,
        "default": "stable",
        "expiry": expiry,
        "token": get_token(["csrf"])["csrftoken"]
    }

    try:
        session.post(params)
    except:
        logger.error("failed to stabilize check crasreport for details")
        logger.critical(traceback.format_exc())
        return False

    return True

def get_latest_rev(title):
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvprop": "ids",
    }
    query = session.get(params)["query"]["pages"]

    for pageid in query:
        if pageid == "-1":
            return False
        if "revisions" not in query[pageid]:
            return False
        return query[pageid]["revisions"][0]["revid"]

    return False

def get_sha1(revid):
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

def get_text(title):
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvprop": "content",
        "rvslots": "main"
    }
    query = session.get(params)["query"]["pages"]
    for pageid in query:
        if pageid == "-1":
            return False
        if "revisions" not in query[pageid]:
            return False
        return query[pageid]["revisions"][0]["slots"]["main"]["*"]

    return False

def get_text_by_id(revid):
    params = {
        "action": "query",
        "prop": "revisions",
        "revids": revid,
        "rvprop": "content",
        "rvslots": "main"
    }
    query = session.get(params)["query"]["pages"]
    for pageid in query:
        if pageid == "-1":
            return False
        if "revisions" not in query[pageid]:
            return False
        return query[pageid]["revisions"][0]["slots"]["main"]["*"]

    return False

def get_page_history(title, **kwargs):
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvprop": "ids|timestamp|flags|comment|user",
        "rvslots": "main"
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

def get_user_rights(user):
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

def is_reverted(title, revid):
    pick = False

    revisions = get_page_history(title, rvprop="ids|sha1", rvlimit=10)
    for rev in revisions:
        if str(rev["revid"]) == str(revid):
            return False

        for drev in revisions:
            if str(drev["revid"]) == str(revid):
                pick = True
                continue
            if not pick:
                continue

            if rev["sha1"] == drev["sha1"]:
                return True

        pick = False

    return False

def get_stable_log(title, timestamp=None):
    params = {
        "action": "query",
        "list": "logevents",
        "letype": "stable",
        "letitle": title
    }
    if timestamp:
        query = session.get(params, leend=timestamp)
        return query
    else:
        query = session.get(params)
        return query

    return False

def save_page(title, text, comment, minor=False):
    params = {
        "action": "edit",
        "title": title,
        "text": text,
        "summary": comment,
        "minor": minor,
        "bot": True,
        "token": get_token(["csrf"])["csrftoken"]
    }
    session.post(params)
    return True
