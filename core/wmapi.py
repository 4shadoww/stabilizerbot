
# Import core modules
import core.config

class ORES:
	base_url = "https://ores.wikimedia.org/scores/"+core.config.lang+"wiki"
	revids_url = "?revids="
	models_url = "&models="

	def parameterMaker(self, base, values):
		final_str = base
		for i in range(len(values)):
			final_str += values[i]

			if i < len(values) - 1:
				final_str += "|"

		return final_str

	def getScore(self, revids, models):
		request_url = self.base_url+self.parameterMaker(self.revids_url, revids)+self.parameterMaker(self.models_url, models)
		print(request_url)
