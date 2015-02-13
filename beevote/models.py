from google.appengine.ext import db

import datetime

# Start of Data Model

class BeeVoteUser(db.Model):
	name = db.StringProperty()
	surname = db.StringProperty()
	user_id = db.StringProperty()
	email = db.StringProperty(required=True)
	creation = db.DateTimeProperty(auto_now_add=True)
	img = db.BlobProperty()
	
	@staticmethod
	def get_from_id(beevote_user_id):
		beevote_user_key = db.Key.from_path('BeeVoteUser', long(beevote_user_id))
		beevote_user = db.get(beevote_user_key)
		return beevote_user
	
	def get_groups_by_membership(self):
		groups = db.GqlQuery("SELECT * FROM Group").fetch(1000)
		groups = [g for g in groups if not (not self.key() in g.members) and (g.members != [])]
		return groups

class RegistrationRequest(db.Model):
	user_id = db.StringProperty()
	email = db.StringProperty()
	name = db.StringProperty()
	surname = db.StringProperty()
	creation = db.DateTimeProperty(auto_now_add=True)

class Group(db.Model):
	name = db.StringProperty(required=True)
	description = db.TextProperty()
	members = db.ListProperty(db.Key) # BeeVoteUser Key
	admins = db.ListProperty(db.Key) # BeeVoteUser Key
	creator = db.ReferenceProperty(BeeVoteUser, required=True)
	img = db.BlobProperty()
	creation = db.DateTimeProperty(auto_now_add=True)
	
	@staticmethod
	def get_from_id(group_id):
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		return group
	
	@staticmethod
	def create(name, creator, description="", img=""):
		group = Group(
				name = name,
				creator = creator,
				description = description,
			)
		if img != "":
			group.img = db.Blob(img)
		group.members.append(creator.key())
		group.admins.append(creator.key())
		return group
	
	def get_topics(self):
		return db.GqlQuery('SELECT * FROM Topic WHERE group = :1', self).fetch(1000)
	
	def get_members(self):
		return db.get(self.members)

	def get_admins(self):
		return db.get(self.admins)
	
	def delete(self):
		topics = self.get_topics()
		for topic in topics:
			topic.delete()
		db.Model.delete(self)

class Topic(db.Model):
	title = db.StringProperty(required=True)
	group = db.ReferenceProperty(Group, required=True)
	description = db.TextProperty()
	place = db.StringProperty()
	date = db.DateProperty()
	time = db.TimeProperty()
	deadline = db.DateTimeProperty()
	creator = db.ReferenceProperty(BeeVoteUser, required=True)
	img = db.BlobProperty()
	creation = db.DateTimeProperty(auto_now_add=True)
	
	@staticmethod
	def get_from_id(group_id, topic_id):
		topic_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id))
		topic = db.get(topic_key)
		return topic
	
	@staticmethod
	def create(title, group, creator, place="", date="", time="", deadline="", description="", img=""):
		topic = Topic(
			title=title,
			group=group,
			parent=group,
			creator=creator,
			  )
		topic.place = place
		if date != "":
			topic.date = datetime.datetime.strptime(date, "%d/%m/%Y").date()
		if time != "":
			topic.time = datetime.datetime.strptime(time, '%H:%M').time()
		if deadline !="":
			topic.deadline = datetime.datetime.strptime(deadline, "%d/%m/%Y %H:%M")
		topic.description = description
		if img != "":
			topic.img = db.Blob(img)
		return topic
	
	def get_proposals(self):
		return db.GqlQuery('SELECT * FROM Proposal WHERE topic = :1', self).fetch(1000)
	
	def delete(self):
		proposals = self.get_proposals()
		for proposal in proposals:
			proposal.delete()
		db.Model.delete(self)

class Proposal(db.Model):
	title = db.StringProperty(required=True)
	topic = db.ReferenceProperty(Topic, required=True)
	description = db.TextProperty()
	place = db.StringProperty()
	date = db.DateProperty()
	time = db.TimeProperty()
	creator = db.ReferenceProperty(BeeVoteUser, required=True)
	creation = db.DateTimeProperty(auto_now_add=True)
	
	@staticmethod
	def get_from_id(group_id, topic_id, proposal_id):
		proposal_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id), 'Proposal', long(proposal_id))
		proposal = db.get(proposal_key)
		return proposal
	
	def get_votes(self):
		return db.GqlQuery('SELECT * FROM Vote WHERE proposal = :1', self).fetch(1000)
	
	def delete(self):
		votes = self.get_votes()
		for vote in votes:
			vote.delete()
		db.Model.delete(self)
	
class Vote(db.Model):
	proposal = db.ReferenceProperty(Proposal, required=True)
	creator = db.ReferenceProperty(BeeVoteUser, required=True)

class FeatureChange(db.Model):
	description = db.StringProperty(required=True)
	creation = db.DateTimeProperty(auto_now_add=True)

# End of Data Model

# Start of functions

def get_beevote_user_from_google_id(user_id):
	return db.GqlQuery('SELECT * FROM BeeVoteUser WHERE user_id = :1', user_id).get()

def get_registration_request_from_google_id(user_id):
	return db.GqlQuery('SELECT * FROM RegistrationRequest WHERE user_id = :1', user_id).get()

# End of functions