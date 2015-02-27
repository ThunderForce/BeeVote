from google.appengine.ext import db
from google.appengine.api import memcache

import datetime

# Start of Data Model

class BeeVoteUser(db.Model):
	name = db.StringProperty()
	surname = db.StringProperty()
	user_id = db.StringProperty()
	email = db.StringProperty(required=True)
	creation = db.DateTimeProperty(auto_now_add=True)
	img = db.BlobProperty()
	last_access = db.DateTimeProperty()
	language = db.StringProperty()
	
	@staticmethod
	def get_from_id(beevote_user_id):
		beevote_user = memcache.get('beevoteuser_by_id_%s' % beevote_user_id)  # @UndefinedVariable
		if beevote_user is None:
			beevote_user_key = db.Key.from_path('BeeVoteUser', long(beevote_user_id))
			beevote_user = db.get(beevote_user_key)
			memcache.add('beevoteuser_by_id_%s' % beevote_user_id, beevote_user, time=600)  # @UndefinedVariable
		return beevote_user
	
	def get_groups_by_membership(self):
		groups = db.GqlQuery("SELECT * FROM Group").fetch(1000)
		groups = [g for g in groups if not (not self.key() in g.members) and (g.members != [])]
		return groups
	
	def get_topics_by_group_membership(self):
		groups = self.get_groups_by_membership()
		topics = []
		for group in groups:
			group_topics = group.get_topics()
			for topic in group_topics:
				topics.append(topic)
		return topics
	
	def put(self):
		db.Model.put(self)
		if not memcache.replace('beevoteuser_by_id_%s' % self.key().id(), self, time=600):  # @UndefinedVariable
			memcache.add('beevoteuser_by_id_%s' % self.key().id(), self, time=600)  # @UndefinedVariable
		if not memcache.replace('beevoteuser_by_user_id_%s' % self.user_id, self, time=600):  # @UndefinedVariable
			memcache.add('beevoteuser_by_user_id_%s' % self.user_id, self, time=600)  # @UndefinedVariable

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
	last_change = db.DateTimeProperty(auto_now=True)
	
	@staticmethod
	def get_from_id(group_id):
		group = memcache.get('group_by_id_%s' % group_id)  # @UndefinedVariable
		if group is None:
			group_key = db.Key.from_path('Group', long(group_id))
			group = db.get(group_key)
			memcache.add('group_by_id_%s' % group_id, group, time=600)  # @UndefinedVariable
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
		memcache.delete('group_by_id_%s' % self.key().id())  # @UndefinedVariable
		db.Model.delete(self)

	def put(self):
		db.Model.put(self)
		if not memcache.replace('group_by_id_%s' % self.key().id(), self, time=600):  # @UndefinedVariable
			memcache.add('group_by_id_%s' % self.key().id(), self, time=600)  # @UndefinedVariable

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
	non_participant_users = db.ListProperty(db.Key) # BeeVoteUser Key
	last_change = db.DateTimeProperty(auto_now=True)
	
	@staticmethod
	def get_from_id(group_id, topic_id):
		topic = memcache.get('topic_by_path_%s_%s' % (group_id, topic_id))  # @UndefinedVariable
		if topic is None:
			topic_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id))
			topic = db.get(topic_key)
			memcache.add('topic_by_path_%s_%s' % (group_id, topic_id), topic, time=600)  # @UndefinedVariable
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
			if topic.date.year <= 1900:
				raise Exception('Year cannot be before 1900')
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
		memcache.delete('topic_by_path_%s_%s' % (self.group.key().id(), self.key().id()))  # @UndefinedVariable
		db.Model.delete(self)

	def put(self):
		db.Model.put(self)
		if not memcache.replace('topic_by_path_%s_%s' % (self.group.key().id(), self.key().id()), self, time=600):  # @UndefinedVariable
			memcache.add('topic_by_path_%s_%s' % (self.group.key().id(), self.key().id()), self, time=600)  # @UndefinedVariable

	def add_non_participant_user(self, beevote_user_key):
		self.non_participant_users.append(beevote_user_key)
	
	def remove_non_participant_user(self, beevote_user_key):
		self.non_participant_users.remove(beevote_user_key)

	def is_user_participant(self, beevote_user):
		return beevote_user.key() not in self.not_participating_users
	

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
		proposal = memcache.get('proposal_by_path_%s_%s_%s' % (group_id, topic_id, proposal_id))  # @UndefinedVariable
		if proposal is None:
			proposal_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id), 'Proposal', long(proposal_id))
			proposal = db.get(proposal_key)
			memcache.add('proposal_by_path_%s_%s_%s' % (group_id, topic_id, proposal_id), proposal, time=600)  # @UndefinedVariable
		return proposal
	
	def get_votes(self):
		return db.GqlQuery('SELECT * FROM Vote WHERE proposal = :1', self).fetch(1000)
	
	def put(self):
		db.Model.put(self)
		if not memcache.replace('proposal_by_path_%s_%s_%s' % (self.topic.group.key().id(), self.topic.key().id(), self.key().id()), self, time=600):  # @UndefinedVariable
			memcache.add('proposal_by_path_%s_%s_%s' % (self.topic.group.key().id(), self.topic.key().id(), self.key().id()), self, time=600)  # @UndefinedVariable
	
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

class GroupAccess(db.Model):
	beevote_user = db.ReferenceProperty(BeeVoteUser, required=True)
	group = db.ReferenceProperty(Group, required=True)
	timestamp = db.DateTimeProperty()
	@staticmethod
	def get_specific_access(group, beevote_user):
		return db.GqlQuery("SELECT * FROM GroupAccess WHERE group = :1 AND beevote_user = :2", group, beevote_user).get()
	
	@staticmethod
	def update_specific_access(group, beevote_user):
		access = GroupAccess.get_specific_access(group, beevote_user)
		if not access:
			access = GroupAccess(beevote_user=beevote_user, group=group)
		access.timestamp = datetime.datetime.now()
		access.put()

class TopicAccess(db.Model):
	beevote_user = db.ReferenceProperty(BeeVoteUser, required=True)
	topic = db.ReferenceProperty(Topic, required=True)
	timestamp = db.DateTimeProperty()
	@staticmethod
	def get_specific_access(topic, beevote_user):
		return db.GqlQuery("SELECT * FROM TopicAccess WHERE topic = :1 AND beevote_user = :2", topic, beevote_user).get()
	
	@staticmethod
	def update_specific_access(topic, beevote_user):
		access = GroupAccess.get_specific_access(topic, beevote_user)
		if not access:
			access = TopicAccess(beevote_user=beevote_user, topic=topic)
		access.timestamp = datetime.datetime.now()
		access.put()

class GroupNotification(db.Model):
	GROUP_INVITATION = 0
	GROUP_NAME_CHANGE = 1
	GROUP_DESCRIPTION_CHANGE = 2
	TOPIC_CREATION = 3
	TOPIC_EXPIRATION = 4
	group = db.ReferenceProperty(Group, required=True)
	notification_code = db.IntegerProperty(required=True)
	beevote_user = db.ReferenceProperty(BeeVoteUser, required=False)
	timestamp = db.DateTimeProperty(auto_now_add=True)
	
	@staticmethod
	def get_for_beevote_user(beevote_user):
		groups = beevote_user.get_groups_by_membership()
		all_notifications = {}
		for group in groups:
			group_access = GroupAccess.get_specific_access(group, beevote_user)
			if group_access:
				timestamp = group_access.timestamp
			elif beevote_user.last_access:
				timestamp = beevote_user.last_access
			else:
				timestamp = datetime.datetime.min
			group_notifications = GroupNotification.get_from_timestamp(timestamp, group, beevote_user)
			all_notifications[str(group.key().id())] = group_notifications
		return all_notifications
	
	@staticmethod
	def get_from_timestamp(timestamp, group=None, beevote_user=None):
		# TODO order results
		if group:
			notifications = db.GqlQuery("SELECT * FROM GroupNotification WHERE timestamp > :1 AND group = :2", timestamp, group).fetch(1000)
		else:
			notifications = db.GqlQuery("SELECT * FROM GroupNotification WHERE timestamp > :1", timestamp).fetch(1000)
		if beevote_user:
			return [n for n in notifications if not n.beevote_user or (beevote_user and beevote_user.key() == n.beevote_user.key())]
		else:
			return notifications
	
	@staticmethod
	def create(notification_code, group, beevote_user=None):
		notification = GroupNotification(
			notification_code=notification_code,
			group=group,
			beevote_user=beevote_user
		)
		notification.put()

class TopicNotification(db.Model):
	TOPIC_CREATION = 0
	PROPOSAL_CREATION = 1
	TOPIC_EXPIRATION = 2
	topic = db.ReferenceProperty(Topic, required=True)
	notification_code = db.IntegerProperty(required=True)
	beevote_user = db.ReferenceProperty(BeeVoteUser, required=False)
	timestamp = db.DateTimeProperty(auto_now_add=True)
	
	@staticmethod
	def get_for_beevote_user(beevote_user):
		topics = beevote_user.get_topics_by_group_membership()
		all_notifications = {}
		for topic in topics:
			topic_access = TopicAccess.get_specific_access(topic, beevote_user)
			if topic_access:
				timestamp = topic_access.timestamp
			elif beevote_user.last_access:
				timestamp = beevote_user.last_access
			else:
				timestamp = datetime.datetime.min
			topic_notifications = TopicNotification.get_from_timestamp(timestamp, topic, beevote_user)
			all_notifications[str(topic.group.key().id()) + '-' + str(topic.key().id())] = topic_notifications
		return all_notifications
	
	@staticmethod
	def get_from_timestamp(timestamp, topic=None, beevote_user=None):
		# TODO order results
		if topic:
			notifications = db.GqlQuery("SELECT * FROM TopicNotification WHERE timestamp > :1 AND topic = :2", timestamp, topic).fetch(1000)
		else:
			notifications = db.GqlQuery("SELECT * FROM TopicNotification WHERE timestamp > :1", timestamp).fetch(1000)
		if beevote_user:
			return [n for n in notifications if not n.beevote_user or (beevote_user and beevote_user.key() == n.beevote_user.key())]
		else:
			return notifications
	
	@staticmethod
	def create(notification_code, topic, beevote_user=None):
		notification = TopicNotification(
			notification_code=notification_code,
			topic=topic,
			beevote_user=beevote_user
		)
		notification.put()

# End of Data Model

# Start of functions

def get_beevote_user_from_google_id(user_id):
	beevote_user = memcache.get('beevoteuser_by_user_id_%s' % user_id)  # @UndefinedVariable
	if beevote_user is None:
		beevote_user =  db.GqlQuery('SELECT * FROM BeeVoteUser WHERE user_id = :1', user_id).get()
		memcache.add('beevoteuser_by_user_id_%s' % user_id, beevote_user, time=600)  # @UndefinedVariable
	return beevote_user

def get_registration_request_from_google_id(user_id):
	return db.GqlQuery('SELECT * FROM RegistrationRequest WHERE user_id = :1', user_id).get()

# End of functions