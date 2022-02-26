import json
import ipaddress

from core.rule_core import *
from core import yapi as api

class RuleModule:

    name = "ipspace"
    cfg_ver = None

    config = {
        "expiry": 24,
        "score": 1,
        "list_path": "Käyttäjä:VakauttajaBot/greylist.json"
    }

    list_ver = None
    greylist = None

    def run(self, rev):
        score = 0
        expiry = None

        lastrev = api.get_latest_rev(self.config["list_path"])

        if not lastrev:
            logger.critical("greylist not found")
            return score, expiry

        if lastrev != self.list_ver:
            self.greylist = json.loads(api.get_text(self.config["list_path"]))
            self.list_ver = lastrev

        for address in self.greylist["values"]:
            try:
                user = ipaddress.ip_address(rev["user"])
            except ValueError:
                continue

            if user in ipaddress.ip_network(address):
                score = self.config["score"]
                expiry = self.config["expiry"]
                break

        return score, expiry
