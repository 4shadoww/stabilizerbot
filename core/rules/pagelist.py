import json

from core.rule_core import *
from core import yapi

class RuleModule:

    name = "pagelist"
    cfg_ver = None


    config = {
        "expiry": 24,
        "score": 1,
        "list_path": "Käyttäjä:VakauttajaBot/greylist.json"
    }

    list_ver = None
    api = yapi.MWAPI
    greylist = None

    def run(self, rev):
        score = 0
        expiry = None

        lastrev = self.api.get_latest_rev(self.config["list_path"])

        if not lastrev:
            logger.critical("greylist not found")
            return score, expiry

        if lastrev != self.list_ver:
            self.greylist = json.loads(self.api.get_text(self.config["list_path"]))
            self.list_ver = lastrev

        for title in self.greylist["values"]:
            if title.replace("_", "") == rev["title"]:
                score = self.config["score"]
                expiry = self.config["expiry"]
                break

        return score, expiry
