# Import python modules
import datetime
import logging

from core import timelib
from core import yapi

logger = logging.getLogger("infolog")
api = yapi.MWAPI

# Get reverts from article
def get_reverts(title, hours=1):
    reverts = []

    end = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
    edits = api.get_page_history(title, rvprop="timestamp|user|content|ids", rvend=timelib.to_string(end))
    if not edits:
        logger.error("failed to receive edits end: %s, title: %s" % (timelib.to_string(end), title))
        return False

    for i in range(len(edits)):
        for x in range(i+1, len(edits)):
            if edits[i]["slots"]["main"]["*"] == edits[x]["slots"]["main"]["*"]:
                revert = {"reverter": edits[i]["user"], "victim": edits[i+1]["user"], "revid": edits[i]["revid"], "oldrevid": edits[i+1]["revid"]}
                reverts.append(revert)
                break
    return reverts
