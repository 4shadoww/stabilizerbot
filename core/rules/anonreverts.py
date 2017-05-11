from core.rule_core import *

class YunoModule:

	def run(self, page):
		edits = op.createEditList(page)
		print(edits[0].timestamp)
		print(op.getRevertCount(edits))
