import json

from core.rule_core import *
from core import yapi

class YunoModule:

    name = "whitelist"
    cfg_ver = None

    config = {
        "score": -1,
        "list_path": "Käyttäjä:VakauttajaBot/whitelist.js"
    }

    list_ver = None
    api = yapi.MWAPI
    whitelist = None

    def run(self, rev):
        score = 0
        expiry = None

        lastrev = self.api.getLatestRev(self.config["list_path"])

        if not lastrev:
            logger.critical("whitelist not found")
            return score, expiry

        if lastrev != self.list_ver:
            self.whitelist = json.loads(self.api.getText(self.config["list_path"]))
            self.list_ver = lastrev

        for user in self.whitelist["values"]:
            if user == rev["user"]:
                score = self.config["score"]
                expiry = 0
                break

        return score, expiry
