
class Edit:
	title = None
	text = None
	user = None
	revid = None
	timestamp = None

	def __init__(self, title, text, user, revid, timestamp):
		self.title = title
		self.text = text
		self.user = user
		self.revid = revid
		self.timestamp = timestamp
