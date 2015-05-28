import datetime
from google.appengine.ext import ndb

from google.appengine.api import memcache

# Start of Data Model

class BeeVoteUser(ndb.Model):
	name = ndb.StringProperty()
	surname = ndb.StringProperty()
	user_id = ndb.StringProperty()
	email = ndb.StringProperty(required=True)
	creation = ndb.DateTimeProperty(auto_now_add=True)
	img = ndb.BlobProperty()
	last_access = ndb.DateTimeProperty()
	language = ndb.StringProperty()
	
	@staticmethod
	def get_from_id(beevote_user_id):
		beevote_user = memcache.get('beevoteuser_by_id_%s' % beevote_user_id)  # @UndefinedVariable
		if beevote_user is None:
			beevote_user = BeeVoteUser.get_by_id(beevote_user_id)
			memcache.add('beevoteuser_by_id_%s' % beevote_user_id, beevote_user, time=600)  # @UndefinedVariable
		return beevote_user
	
	@staticmethod
	def get_from_google_id(user_id):
		beevote_user = memcache.get('beevoteuser_by_user_id_%s' % user_id)  # @UndefinedVariable
		if beevote_user is None:
			beevote_user =  ndb.gql('SELECT * FROM BeeVoteUser WHERE user_id = :1', user_id).get()
			memcache.add('beevoteuser_by_user_id_%s' % user_id, beevote_user, time=600)  # @UndefinedVariable
		return beevote_user
	
	@staticmethod
	def get_by_email(email):
		return BeeVoteUser.query(BeeVoteUser.email == email).get()
	
	@staticmethod
	def get_all():
		return ndb.gql("SELECT * FROM BeeVoteUser").fetch(1000)
	
	@staticmethod
	def get_from_keys(keys):
		return ndb.get_multi(keys)
	
	def get_groups_by_membership(self):
		return Group.query(Group.members == self.key).order(Group.name).fetch(1000)
	
	def get_topics_by_group_membership(self):
		groups = self.get_groups_by_membership()
		topics = []
		for group in groups:
			group_topics = group.get_topics()
			for topic in group_topics:
				topics.append(topic)
		return topics
	
	def put(self):
		ndb.Model.put(self)
		if not memcache.replace('beevoteuser_by_id_%s' % self.key.id(), self, time=600):  # @UndefinedVariable
			memcache.add('beevoteuser_by_id_%s' % self.key.id(), self, time=600)  # @UndefinedVariable
		if not memcache.replace('beevoteuser_by_user_id_%s' % self.user_id, self, time=600):  # @UndefinedVariable
			memcache.add('beevoteuser_by_user_id_%s' % self.user_id, self, time=600)  # @UndefinedVariable

class Group(ndb.Model):
	name = ndb.StringProperty(required=True)
	description = ndb.TextProperty()
	members = ndb.KeyProperty(kind=BeeVoteUser, repeated=True) # BeeVoteUser Key
	admins = ndb.KeyProperty(kind=BeeVoteUser, repeated=True) # BeeVoteUser Key
	creator = ndb.KeyProperty(kind=BeeVoteUser, required=False)
	img = ndb.BlobProperty()
	creation = ndb.DateTimeProperty(auto_now_add=True)
	last_change = ndb.DateTimeProperty(auto_now=True)
	
	@staticmethod
	def get_from_id(group_id):
		return Group.get_by_id(long(group_id))
		'''
		group = memcache.get('group_by_id_%s' % group_id)  # @UndefinedVariable
		if group is None:
			group = Group.get_by_id(group_id)
			memcache.add('group_by_id_%s' % group_id, group, time=600)  # @UndefinedVariable
		return group
		'''
	
	@staticmethod
	def create(name, creator_key, description="", img=""):
		group = Group(
				name = name,
				creator = creator_key,
				description = description,
			)
		if img != "":
			group.img = img
		group.members.append(creator_key)
		group.admins.append(creator_key)
		return group
	
	def get_topics(self):
		return Topic.query(Topic.group == self.key).fetch(1000)
	
	def get_members(self):
		return ndb.get_multi(self.members)

	def contains_user(self, beevote_user):
		if self.members == [] or beevote_user.key in self.members:
			return True
		else:
			return False

	def get_admins(self):
		return ndb.get_multi(self.admins)
	
	def get_notifications_for_user(self, beevote_user):
		last_access = GroupAccess.get_specific_access(self, beevote_user)
		group_notifications = GroupNotification.get_from_timestamp(last_access.timestamp, group=self, beevote_user=beevote_user)
		topics_notifications = TopicNotification.get_for_beevote_user(beevote_user, self.get_topics())
		return {
			'group_notifications': group_notifications,
			'topics_notifications': topics_notifications[self.key.id()],
		}
	
	def delete(self):
		topics = self.get_topics()
		for topic in topics:
			topic.delete()
		'''
		memcache.delete('group_by_id_%s' % self.key.id())  # @UndefinedVariable
		'''
		self.key.delete()

	'''
	def put(self):
		db.Model.put(self)
		if not memcache.replace('group_by_id_%s' % self.key().id(), self, time=600):  # @UndefinedVariable
			memcache.add('group_by_id_%s' % self.key().id(), self, time=600)  # @UndefinedVariable
	'''

class Topic(ndb.Model):
	title = ndb.StringProperty(required=True)
	group = ndb.KeyProperty(kind=Group, required=True)
	description = ndb.TextProperty()
	place = ndb.StringProperty()
	date = ndb.DateProperty()
	time = ndb.TimeProperty()
	deadline = ndb.DateTimeProperty()
	creator = ndb.KeyProperty(kind=BeeVoteUser, required=False)
	img = ndb.BlobProperty()
	creation = ndb.DateTimeProperty(auto_now_add=True)
	non_participant_users = ndb.KeyProperty(kind=BeeVoteUser, repeated=True) # BeeVoteUser Key
	last_change = ndb.DateTimeProperty(auto_now=True)
	
	@staticmethod
	def get_from_id(group_id, topic_id):
		return ndb.Key('Group', long(group_id), 'Topic', long(topic_id)).get()
		'''
		topic = memcache.get('topic_by_path_%s_%s' % (group_id, topic_id))  # @UndefinedVariable
		if topic is None:
			topic = ndb.Key('Group', group_id, 'Topic', topic_id).get()
			memcache.add('topic_by_path_%s_%s' % (group_id, topic_id), topic, time=600)  # @UndefinedVariable
		return topic
		'''
	
	@staticmethod
	def get_for_groups(groups):
		groups_keys = [g.key for g in groups]
		all_topics = Topic.all().fetch(1000)
		topics = [t for t in all_topics if t.group in groups_keys]
		return topics
	
	@staticmethod
	def create(title, group_key, creator_key, place="", date="", time="", deadline="", description="", img=""):
		topic = Topic(
			title=title,
			group=group_key,
			parent=group_key,
			creator=creator_key,
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
			topic.img = img
		return topic
	
	def get_proposals(self):
		return Proposal.query(Proposal.topic == self.key).fetch(1000)
	
	def get_notifications_for_user(self, beevote_user):
		last_access = TopicAccess.get_specific_access(self, beevote_user)
		notifications = TopicNotification.get_from_timestamp(last_access.timestamp, topic=self)
		return notifications
	
	def delete_votes_by_user(self, beevote_user):
		beevote_user_key = beevote_user.key
		proposals = self.get_proposals()
		for proposal in proposals:
			votes = ndb.gql("SELECT * FROM Vote WHERE proposal = :1 AND creator = :2", proposal.key, beevote_user_key)
			for vote in votes:
				vote.key.delete()
	
	def delete(self):
		proposals = self.get_proposals()
		for proposal in proposals:
			proposal.delete()
		# memcache.delete('topic_by_path_%s_%s' % (self.group.key().id(), self.key().id()))  # @UndefinedVariable
		self.key.delete()

	'''
	def put(self):
		db.Model.put(self)
		if not memcache.replace('topic_by_path_%s_%s' % (self.group.key().id(), self.key().id()), self, time=600):  # @UndefinedVariable
			memcache.add('topic_by_path_%s_%s' % (self.group.key().id(), self.key().id()), self, time=600)  # @UndefinedVariable
	'''

	def add_non_participant_user(self, beevote_user_key):
		self.non_participant_users.append(beevote_user_key)
	
	def remove_non_participant_user(self, beevote_user_key):
		self.non_participant_users.remove(beevote_user_key)

	def is_user_participant(self, beevote_user):
		return beevote_user.key not in self.not_participating_users
	

class Proposal(ndb.Model):
	title = ndb.StringProperty(required=True)
	topic = ndb.KeyProperty(kind=Topic, required=True)
	description = ndb.TextProperty()
	place = ndb.StringProperty()
	date = ndb.DateProperty()
	time = ndb.TimeProperty()
	creator = ndb.KeyProperty(kind=BeeVoteUser, required=False)
	creation = ndb.DateTimeProperty(auto_now_add=True)
	
	@staticmethod
	def get_from_id(group_id, topic_id, proposal_id):
		return ndb.Key('Group', long(group_id), 'Topic', long(topic_id), 'Proposal', long(proposal_id)).get()
		'''
		proposal = memcache.get('proposal_by_path_%s_%s_%s' % (group_id, topic_id, proposal_id))  # @UndefinedVariable
		if proposal is None:
			proposal = ndb.Key('Group', group_id, 'Topic', topic_id, 'Proposal', proposal_id).get()
			memcache.add('proposal_by_path_%s_%s_%s' % (group_id, topic_id, proposal_id), proposal, time=600)  # @UndefinedVariable
		return proposal
		'''
	
	def get_votes(self):
		return Vote.query(Vote.proposal == self.key).fetch(1000)
	
	def get_comments(self):
		return ndb.gql("SELECT * FROM ProposalComment WHERE proposal = :1 ORDER BY creation ASC", self.key).fetch(1000)
	
	def remove_user_vote(self, beevote_user):
		votes = ndb.gql("SELECT * FROM Vote WHERE proposal = :1 AND creator = :2", self.key, beevote_user.key)
		for vote in votes:
			vote.key.delete()
	
	'''
	def put(self):
		db.Model.put(self)
		if not memcache.replace('proposal_by_path_%s_%s_%s' % (self.topic.group.key().id(), self.topic.key().id(), self.key().id()), self, time=600):  # @UndefinedVariable
			memcache.add('proposal_by_path_%s_%s_%s' % (self.topic.group.key().id(), self.topic.key().id(), self.key().id()), self, time=600)  # @UndefinedVariable
	'''
	
	def delete(self):
		votes = self.get_votes()
		for vote in votes:
			vote.delete()
		self.key.delete()

class ProposalComment(ndb.Model):
	proposal = ndb.KeyProperty(kind=Proposal, required=True)
	description = ndb.TextProperty()
	creator = ndb.KeyProperty(kind=BeeVoteUser, required=False)
	creation = ndb.DateTimeProperty(auto_now_add=True)

class Vote(ndb.Model):
	proposal = ndb.KeyProperty(kind=Proposal, required=True)
	creator = ndb.KeyProperty(kind=BeeVoteUser, required=False)

class FeatureChange(ndb.Model):
	description = ndb.StringProperty(required=True)
	creation = ndb.DateTimeProperty(auto_now_add=True)
	
	@staticmethod
	def get_from_date(date):
		return ndb.gql("SELECT * FROM FeatureChange WHERE creation > :1", date).fetch(1000)

class GroupAccess(ndb.Model):
	beevote_user = ndb.KeyProperty(kind=BeeVoteUser, required=True)
	group = ndb.KeyProperty(kind=Group, required=True)
	timestamp = ndb.DateTimeProperty()
	@staticmethod
	def get_specific_access(group, beevote_user):
		return ndb.gql("SELECT timestamp FROM GroupAccess WHERE group = :1 AND beevote_user = :2 ORDER BY timestamp DESC", group.key, beevote_user.key).get()
	
	@staticmethod
	def update_specific_access(group, beevote_user):
		access = ndb.gql("SELECT * FROM GroupAccess WHERE group = :1 AND beevote_user = :2 ORDER BY timestamp DESC", group.key, beevote_user.key).get()
		if not access:
			access = GroupAccess(beevote_user=beevote_user.key, group=group.key)
		access.timestamp = datetime.datetime.now()
		access.put()

class TopicAccess(ndb.Model):
	beevote_user = ndb.KeyProperty(kind=BeeVoteUser, required=True)
	topic = ndb.KeyProperty(kind=Topic, required=True)
	timestamp = ndb.DateTimeProperty()
	@staticmethod
	def get_specific_access(topic, beevote_user):
		return ndb.gql("SELECT timestamp FROM TopicAccess WHERE topic = :1 AND beevote_user = :2 ORDER BY timestamp DESC", topic.key, beevote_user.key).get()
	
	@staticmethod
	def update_specific_access(topic, beevote_user):
		access = ndb.gql("SELECT * FROM TopicAccess WHERE topic = :1 AND beevote_user = :2 ORDER BY timestamp DESC", topic.key, beevote_user.key).get()
		if not access:
			access = TopicAccess(beevote_user=beevote_user.key, topic=topic.key)
		access.timestamp = datetime.datetime.now()
		access.put()

class GroupNotification(ndb.Model):
	GROUP_INVITATION = 'group_invitation'
	GROUP_NAME_CHANGE = 'group_name_change'
	GROUP_DESCRIPTION_CHANGE = 'group_description_change'
	GROUP_IMAGE_CHANGE = 'group_image_change'
	group = ndb.KeyProperty(kind=Group, required=True)
	notification_code = ndb.StringProperty(required=True)
	beevote_user = ndb.KeyProperty(kind=BeeVoteUser, required=False)
	timestamp = ndb.DateTimeProperty(auto_now_add=True)
	
	@staticmethod
	def get_for_beevote_user(beevote_user, groups):
		'''
		{
			'group_1_id': {
				'group_notifications': [
					... group notifications
				],
				'number_of_topics_with_notifications': int
			},
			'group_2_id': {
				'group_notifications': [
					... group notifications
				],
				'number_of_topics_with_notifications': int
			},
			...
			
		}
		'''
		
		groups_notifications = []
		for group in groups:
			g_a = GroupAccess.get_specific_access(group, beevote_user)
			if g_a:
				timestamp = g_a.timestamp
			else:
				timestamp = datetime.datetime.min
			g_n = ndb.gql("SELECT * FROM GroupNotification WHERE group = :1 AND timestamp > :2", group.key, timestamp).fetch(1000)
			for n in g_n:
				groups_notifications.append(n)
		
		notifications_by_group = {}
		for notif in groups_notifications:
			group_id = notif.topic.get().group.key.id()
			if not group_id in notifications_by_group.keys():
				notifications_by_group[group_id] = {'group_notifications': []}
			notifications_by_group[group_id]['group_notifications'].append(notif)
		
		topics = Topic.get_for_groups(groups)
		topics_notifications = TopicNotification.get_for_beevote_user(beevote_user, topics)
		
		for group_id in topics_notifications.keys():
			notifications_by_group[group_id]['number_of_topics_with_notifications'] = len(topics_notifications[group_id].keys())
			
		return notifications_by_group
	
	@staticmethod
	def get_from_timestamp(timestamp, group=None, beevote_user=None):
		# TODO order results
		if group:
			notifications = ndb.gql("SELECT * FROM GroupNotification WHERE timestamp > :1 AND group = :2", timestamp, group.key).fetch(1000)
		else:
			notifications = ndb.gql("SELECT * FROM GroupNotification WHERE timestamp > :1", timestamp).fetch(1000)
		if beevote_user:
			return [n for n in notifications if not n.beevote_user or (beevote_user and beevote_user.key == n.beevote_user)]
		else:
			return notifications
	
	@staticmethod
	def create(notification_code, group_key, beevote_user_key=None):
		notification = GroupNotification(
			notification_code=notification_code,
			group=group_key,
			beevote_user=beevote_user_key
		)
		notification.put()

class TopicNotification(ndb.Model):
	TOPIC_CREATION = 'topic_creation'
	TOPIC_IMAGE_CHANGE = 'topic_image_change'
	PROPOSAL_CREATION = 'proposal_creation'
	TOPIC_EXPIRATION = 'topic_expiration'
	topic = ndb.KeyProperty(kind=Topic, required=True)
	notification_code = ndb.StringProperty(required=True)
	timestamp = ndb.DateTimeProperty(auto_now_add=True)
	
	@staticmethod
	def get_for_beevote_user(beevote_user, topics):
		'''
		{
			'group_1_id': {
				'topic_1_id': [
					... notifications
				],
				'topic_2_id': [
					... notifications
				],
				...
			},
			'group_2_id': {
				'topic_3_id': [
					... notifications
				],
				'topic_4_id': [
					... notifications
				],
				...
			},
			...
			
		}
		'''
		
		topics_notifications = []
		for topic in topics:
			t_a = TopicAccess.get_specific_access(topic, beevote_user)
			if t_a:
				timestamp = t_a.timestamp
			else:
				timestamp = datetime.datetime.min
			t_n = ndb.gql("SELECT * FROM TopicNotification WHERE topic = :1 AND timestamp > :2", topic.key, timestamp).fetch(1000)
			for n in t_n:
				topics_notifications.append(n)
		
		notifications_by_group = {}
		for notif in topics_notifications:
			group_id = notif.topic.get().group.id()
			topic_id = notif.topic.id()
			if not group_id in notifications_by_group.keys():
				notifications_by_group[group_id] = {}
			if not topic_id in notifications_by_group[group_id].keys():
				notifications_by_group[group_id][topic_id] = []
			notifications_by_group[group_id][topic_id].append(notif)
		
		return notifications_by_group
	
	@staticmethod
	def get_from_timestamp(timestamp, topic=None, beevote_user=None):
		# TODO order results
		if topic:
			notifications = ndb.gql("SELECT * FROM TopicNotification WHERE timestamp > :1 AND topic = :2", timestamp, topic.key).fetch(1000)
		else:
			notifications = ndb.gql("SELECT * FROM TopicNotification WHERE timestamp > :1", timestamp).fetch(1000)
		if beevote_user:
			return [n for n in notifications if not n.beevote_user or (beevote_user and beevote_user.key == n.beevote_user)]
		else:
			return notifications
	
	@staticmethod
	def create(notification_code, topic_key):
		notification = TopicNotification(
			notification_code=notification_code,
			topic=topic_key,
		)
		notification.put()

class GroupPersonalSettings(ndb.Model):
	beevote_user = ndb.KeyProperty(kind=BeeVoteUser, required=True)
	group = ndb.KeyProperty(kind=Group, required=True)
	topic_creation_email = ndb.BooleanProperty()
	
	@staticmethod
	def get_settings(beevote_user, group):
		settings = GroupPersonalSettings.query(
			GroupPersonalSettings.beevote_user == beevote_user.key,
			GroupPersonalSettings.group == group.key
		).get()
		if not settings:
			settings = GroupPersonalSettings.create_default_settings(beevote_user, group)
		return settings
	
	@staticmethod
	def create_default_settings(beevote_user, group):
		return GroupPersonalSettings(
			beevote_user=beevote_user.key,
			group=group.key,
			topic_creation_email=False
		)

class TopicPersonalSettings(ndb.Model):
	beevote_user = ndb.KeyProperty(kind=BeeVoteUser, required=True)
	topic = ndb.KeyProperty(kind=Topic, required=True)
	proposal_creation_email = ndb.BooleanProperty()
	
	@staticmethod
	def get_settings(beevote_user, topic):
		settings = TopicPersonalSettings.query(
			TopicPersonalSettings.beevote_user == beevote_user.key,
			TopicPersonalSettings.topic == topic.key
		).get()
		if not settings:
			settings = TopicPersonalSettings.create_default_settings(beevote_user, topic)
		return settings
	
	@staticmethod
	def create_default_settings(beevote_user, topic):
		return TopicPersonalSettings(
			beevote_user=beevote_user.key,
			topic=topic.key,
			proposal_creation_email=False
		)

class BugReport(ndb.Model):
	device = ndb.StringProperty()
	browser = ndb.StringProperty()
	description = ndb.TextProperty()
	occurrence = ndb.DateTimeProperty()
	creation = ndb.DateTimeProperty(auto_now_add=True)
	creator = ndb.KeyProperty(kind=BeeVoteUser, required=False)

# End of Data Model