
class Edit:
	text = None
	user = None
	revid = None
	timestamp = None

	def __init__(self, text, user, revid, timestamp):
		self.text = text
		self.user = user
		self.revid = revid
		self.timestamp = timestamp
