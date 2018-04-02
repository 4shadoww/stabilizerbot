from core.rule_core import *
from core import yapi
import datetime

class YunoModule:

    name = "adminaction"
    cfg_ver = None

    config = {
        "months": 1,
        "stabilizes": 2,
        "list_path": "Käyttäjä:VakauttajaBot/Pitkäaikaista vakautusta vaativat sivut"
    }

    api = yapi.MWAPI

    def addToList(self, rev):
        text = self.api.getText(self.config["list_path"])
        newpage = "* [["+rev["title"]+"]]"
        if(newpage in text):
            return
        text += "\n"+newpage
        logger.info("adding page "+rev["title"]+" to stabilize list")
        self.api.savePage(self.config["list_path"], text, (config_loader.dictionary[config_loader.cur_conf["core"]["lang"]]["editsum"]["LS"] % rev["title"]), minor=True)

    def run(self, rev):
        score = 0
        expiry = None
        leend = datetime.datetime.utcnow() - datetime.timedelta(days=self.config["months"] * 30, hours=0, minutes=0, seconds=0)
        stable_log = self.api.getStableLog(rev["title"], str(leend).split('.', 2)[0])
        if(len(stable_log["query"]["logevents"]) >= self.config["stabilizes"]):
            if(not config_loader.cur_conf["core"]["test"]):
                self.addToList(rev)

        return score, expiry
