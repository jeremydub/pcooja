import os.path
import math
import re

class Log:
	def __init__(self, log_file, message_parser):
		if os.path.exists(log_file):
			self.log_file=log_file
			self.debug=False
			self.parse_message = message_parser
			self.parse_file(log_file)
		else:
			raise IOError("Log file does not exists !")

	def parse_file(self, file):

		nid_to_messages = {}

		for line in open(file, 'r').readlines():
			parts = line.split(":")
			if len(parts) > 2:
				time=int(parts[0])
				node_id=int(parts[1])

				if not nid_to_messages.has_key(node_id):
					nid_to_messages[node_id] = []

				message = self.parse_message(":".join(parts[2:]), node_id, time)
				if message != None:
					nid_to_messages[node_id].append(message)

		self.dico = nid_to_messages

	def get_messages(self, node_id):
		if self.dico.has_key(node_id):
			return self.dico[node_id]
		else:
			return []

	def get_node_ids(self):
		return self.dico.keys()