# Import python modules
import importlib
import sys

sys.path.append("core/lib")

# Import core modules
import core.config
from core.log import *
from core import mwapi

config = {
	"required_score": 2,
}

def load_rules():
	rules = []

	for rule in core.config.rules:
		module = importlib.import_module("core.rules."+rule)
		rules.append(module.YunoModule())

	return rules

def shouldStabilize(rev, rules):
	overall_score = 0

	for rule in rules:
		score = rule.run(rev)
		printlog(rule.name, "on page:", rev["title"],  "score:", score)

		if score < 0:
			return False

		score += overall_score

	if overall_score >= config["required_score"]:
		return True

	return False



def main(rules):
	api = mwapi.MWAPI()
	print(api.getRevision([16504730]))

if __name__ == "__main__":
	rules = load_rules()
	main(rules)
