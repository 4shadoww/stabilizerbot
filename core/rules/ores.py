from core.rule_core import *
from core import yapi as api

from core.config_loader import cur_conf

class RuleModule:

    name = "liftwing"
    cfg_ver = None

    config = [
        {
            "models": {
                "damaging": {"max_false": 0.15, "min_true": 0.8},
                "goodfaith": {"min_false": 0.8, "max_true": 0.15}
            },
            "score": 1,
            "expiry": 24
        }
    ]

    def load_config(self):
        if core.config.config_mode == "online":
            pass

    def get_scores(self, rev):
        tries = 2
        scores = None
        # Check result and check for errors
        # If error faced then try again once
        for i in reversed(range(tries)):
            scores = api.get_score(rev["revision"]["new"])

            for item in scores:
                if "error" in scores[item] and "probability" not in revid_data[item]:
                    if i <= 0:
                        logger.error("failed to fetch liftwing revision data: %s" % str(revid_data))
                        return None
                else:
                    break

        return scores

    def run(self, rev):
        score = 0
        expiry = None

        revid_data = self.get_scores(rev)

        if not revid_data:
            return score, expiry

        for rule in self.config:
            failed = False

            for item in rule["models"]:
                if failed:
                    break

                for value in rule["models"][item]:
                    if value == "max_false" and rule["models"][item][value] < revid_data[item]["probability"]["false"]:
                        failed = True
                        break
                    elif value == "min_false" and rule["models"][item][value] > revid_data[item]["probability"]["false"]:
                        failed = True
                        break
                    elif value == "max_true" and rule["models"][item][value] < revid_data[item]["probability"]["true"]:
                        failed = True
                        break
                    elif value == "min_true" and rule["models"][item][value] > revid_data[item]["probability"]["true"]:
                        failed = True
                        break

            if not failed and rule["score"] > score:
                score = rule["score"]
                expiry = rule["expiry"]

        return score, expiry
