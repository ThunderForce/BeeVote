#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import webapp2
import datetime
import json
import time
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import mail

import collections

import models
from models import GroupNotification, TopicNotification

# Start of constants

max_image_size = 850*1024 # 850 kb

# End of constants

# Start of functions

# TEMPORARY
def is_user_in_group(beevote_user, group):
	if group.members == [] or beevote_user.key() in group.members:
		return True
	else:
		return False
# TEMPORARY

def get_json(json_obj):
	return json.dumps(json_obj, indent=4, separators=(',', ': '))

def fetch_user(beevote_user, arguments):
	user = collections.OrderedDict([
		('data', collections.OrderedDict([
			('id', beevote_user.key().id()),
			('name', beevote_user.name),
			('surname', beevote_user.surname),
			('email', beevote_user.email),
			('has_image', beevote_user.img != None),
			('creation', str(beevote_user.creation)),
		]))
	])
	if 'is_current_user' in arguments and arguments['is_current_user']:
		groups = beevote_user.get_groups_by_membership()
		user['groups'] = fetch_groups(groups, arguments)
	return user

def fetch_group(group, arguments):
	group_json = collections.OrderedDict([
		('data', collections.OrderedDict([
			('id', group.key().id()),
			('name', group.name),
			('description', group.description),
			('has_image', group.img != None),
			('creation', str(group.creation)),
		]))
	])
	if 'fetch_group_members' in arguments and arguments['fetch_group_members']:
		group_json['members'] = fetch_members_from_group(group, arguments)
	if 'fetch_topics' in arguments and arguments['fetch_topics']:
		group_json['topics'] = fetch_topics_from_group(group, arguments)
	return group_json
	
def fetch_topic(topic, arguments):
	topic_dict = collections.OrderedDict([
		('data', collections.OrderedDict([
			('id', topic.key().id()),
			('title', topic.title),
			('description', topic.description),
			('has_image', topic.img != None),
			('place', topic.place if topic.place != "" else None),
			('date', str(topic.date) if topic.date else None),
			('time', str(topic.time) if topic.time else None),
			('deadline', str(topic.deadline) if topic.deadline else None),
			('creator', topic.creator.key().id()),
			('group_id', topic.parent().key().id())
		]))
	])
	if 'evaluate_deadlines' in arguments and arguments['evaluate_deadlines'] and topic.deadline != None:
		currentdatetime = datetime.datetime.now()
		topic_dict['expired'] = topic.deadline < currentdatetime
		time_before_deadline = topic.deadline - currentdatetime
		topic_dict['total_seconds_before_deadline'] = time_before_deadline.total_seconds()
		topic_dict['time_before_deadline'] = collections.OrderedDict([
			('days', time_before_deadline.days),
			('hours', time_before_deadline.seconds/3600),
			('minutes', (time_before_deadline.seconds/60) % 60),
			('seconds', time_before_deadline.seconds % 60),
		])
	if 'fetch_proposals' in arguments and arguments['fetch_proposals']:
		topic_dict['proposals'] = fetch_proposals_from_topic(topic, arguments)
	return topic_dict

def fetch_proposal(proposal, arguments):
	proposal_dict = collections.OrderedDict([
		('id', proposal.key().id()),
		('title', proposal.title),
		('description', proposal.description),
	])
	if 'fetch_votes' in arguments and arguments['fetch_votes']:
		votes = proposal.get_votes()
		proposal_dict['vote_number'] = len(votes)
		proposal_dict['votes'] = fetch_votes(votes, arguments)
	return proposal_dict

def fetch_groups(groups, arguments):
	groups_ret = []
	for datastore_group in groups:
		group = fetch_group(datastore_group, arguments)
		groups_ret.append(group)
	return groups_ret

def fetch_members_from_group(group, arguments):
	datastore_members = group.get_members()
	# TODO
	members = []
	for datastore_member in datastore_members:
		member = fetch_user(datastore_member, arguments)
		members.append(member)
	return members
	
def fetch_topics_from_group(group, arguments):
	datastore_topics = group.get_topics()
	topics = []
	for datastore_topic in datastore_topics:
		topic = fetch_topic(datastore_topic, arguments)
		topics.append(topic)
	topics = sorted(topics, key=lambda topic: topic['total_seconds_before_deadline'] if 'total_seconds_before_deadline' in topic else datetime.timedelta.max.total_seconds())
	return topics
	
def fetch_votes(votes, arguments):
	votes_ret = []
	for datastore_vote in votes:
		vote = fetch_vote(datastore_vote, arguments)
		votes_ret.append(vote)
	return votes_ret

def fetch_vote(vote, arguments):
	vote_dict = collections.OrderedDict([
		('creator', fetch_user(vote.creator, arguments))
	])
	return vote_dict

def fetch_proposals_from_topic(topic, arguments):
	datastore_proposals = topic.get_proposals()
	proposals = []
	for datastore_proposal in datastore_proposals:
		proposal = fetch_proposal(datastore_proposal, arguments)
		proposals.append(proposal)
	#topics = sorted(topics, key=lambda topic: topic['total_seconds_before_deadline'] if 'total_seconds_before_deadline' in topic else datetime.timedelta.max.total_seconds())
	return proposals

# End of functions

# Start of handlers

class BaseApiHandler(webapp2.RequestHandler):
	def __init__(self, request, response):
		self.initialize(request, response)
		
		'''
		if not self.request.path in public_urls:
			user = users.get_current_user()
			if not user:
				url = request.url
				if request.query_string != "":
					url += '?' + request.query_string
				self.redirect(users.create_login_url(url))
				return
			self.beevote_user = models.get_beevote_user_from_google_id(user.user_id())
			if not self.beevote_user:
				registration_request = models.get_registration_request_from_google_id(user.user_id())
				if not registration_request:
					self.redirect("/register")
				else:
					self.redirect("/registration-pending")
		'''
		
		self.response.headers['Content-Type'] = "application/json"
		

class LoadGroupsHandler(BaseApiHandler):
	def get(self):
		user = users.get_current_user()
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		datastore_groups = beevote_user.get_groups_by_membership()
		arguments = {
			'fetch_group_members': self.request.get('fetch_group_members', 'false') == 'true',
			'fetch_topics': self.request.get('fetch_topics', 'false') == 'true',
			'evaluate_deadlines': self.request.get('evaluate_deadlines', 'false') == 'true',
			'fetch_proposals': self.request.get('fetch_proposals', 'false') == 'true',
		}
		groups = fetch_groups(datastore_groups, arguments)
		
		self.response.out.write(get_json(groups))

class LoadGroupHandler(BaseApiHandler):
	def get(self, group_id):
		group = models.Group.get_from_id(group_id)
		if (not group):
			self.abort(404, detail="This group does not exist.")
		'''
		if not is_user_in_group(models.get_beevote_user_from_google_id(user.user_id()), group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		'''
		arguments = {
			'fetch_group_members': self.request.get('fetch_group_members', 'false') == 'true',
			'fetch_topics': self.request.get('fetch_topics', 'false') == 'true',
			'evaluate_deadlines': self.request.get('evaluate_deadlines', 'false') == 'true',
			'fetch_proposals': self.request.get('fetch_proposals', 'false') == 'true',
		}
		
		group_json = fetch_group(group, arguments)
		user = users.get_current_user()
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		models.GroupAccess.update_specific_access(group, beevote_user)
		self.response.out.write(get_json(group_json))

class LoadTopicHandler(BaseApiHandler):
	def get(self, group_id, topic_id):
		group = models.Group.get_from_id(group_id)
		if (not group):
			self.abort(404, detail="This group does not exist.")
		'''
		if not is_user_in_group(models.get_beevote_user_from_google_id(user.user_id()), group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		'''
		arguments = {
			'evaluate_deadlines': self.request.get('evaluate_deadlines', 'false') == 'true',
			'fetch_proposals': self.request.get('fetch_proposals', 'false') == 'true',
			'fetch_votes': self.request.get('fetch_votes', 'false') == 'true',
		}
		
		topic = models.Topic.get_from_id(group_id, topic_id)
		topic_json = fetch_topic(topic, arguments)
		user = users.get_current_user()
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		models.TopicAccess.update_specific_access(topic, beevote_user)
		self.response.out.write(get_json(topic_json))

class LoadProposalHandler(BaseApiHandler):
	def get(self, group_id, topic_id, proposal_id):
		group = models.Group.get_from_id(group_id)
		if (not group):
			self.abort(404, detail="This group does not exist.")
		'''
		if not is_user_in_group(models.get_beevote_user_from_google_id(user.user_id()), group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		'''
		arguments = {
			'fetch_votes': self.request.get('fetch_votes', 'false') == 'true',
			'fetch_users': self.request.get('fetch_users', 'false') == 'true',
		}
		
		proposal = models.Proposal.get_from_id(group_id, topic_id, proposal_id)
		proposal_json = fetch_proposal(proposal, arguments)
		
		self.response.out.write(get_json(proposal_json))

class LoadParticipantsHandler(BaseApiHandler):
	def get(self, group_id, topic_id):
		group = models.Group.get_from_id(group_id)
		if (not group):
			self.abort(404, detail="This group does not exist.")
		'''
		if not is_user_in_group(models.get_beevote_user_from_google_id(user.user_id()), group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		'''
		topic =models.Topic.get_from_id(group_id, topic_id)

		arguments = {
			'fetch_users': self.request.get('fetch_users', 'false') == 'true',
		}

		participants=[part for part in group.members if part not in topic.non_participant_users]
		
		beevote_users = models.BeeVoteUser.get(participants)
		json_users = []
		for user in beevote_users:
			json_users.append(fetch_user(user, arguments))
		
		self.response.out.write(get_json(json_users))


class LoadUserHandler(BaseApiHandler):
	def get(self, user_id):
		user = users.get_current_user()
		current_beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		
		target_beevote_user = models.BeeVoteUser.get_from_id(user_id)
		
		arguments = {
			'is_current_user': target_beevote_user.key() == current_beevote_user.key()
		}
		
		beevote_user_ret = fetch_user(target_beevote_user, arguments)
		
		self.response.out.write(get_json(beevote_user_ret))

class CreateVoteHandler(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		group_id = self.request.get('group_id')
		topic_id = self.request.get('topic_id')
		proposal_id = self.request.get('proposal_id')
		proposal_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id), 'Proposal', long(proposal_id))
		proposal = db.get(proposal_key)
		success = True
		if proposal.parent().deadline != None:
			currentdatetime = datetime.datetime.now()
			proposal.parent().expired = proposal.parent().deadline < currentdatetime
			if proposal.parent().expired:
				success = False
		if success:
			user_id = user.user_id()
			beevote_user = models.get_beevote_user_from_google_id(user_id)
			vote = models.Vote(
				proposal = proposal,
				parent=proposal,
				creator = beevote_user
			)
			vote.put()
			time.sleep(0.25)
		votes = db.GqlQuery("SELECT * FROM Vote WHERE proposal = :1", proposal)
		vote_number = votes.count()
		values = {
			'success': success,
			'vote_number': vote_number
		}
		self.response.out.write(json.dumps(values))

class RemoveVoteHandler(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		user_id = user.user_id()
		beevote_user = models.get_beevote_user_from_google_id(user_id)
		group_id = self.request.get('group_id')
		topic_id = self.request.get('topic_id')
		proposal_id = self.request.get('proposal_id')
		proposal_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id), 'Proposal', long(proposal_id))
		proposal = db.get(proposal_key)
		success = True
		if proposal.parent().deadline != None:
			currentdatetime = datetime.datetime.now()
			proposal.parent().expired = proposal.parent().deadline < currentdatetime
			if proposal.parent().expired:
				success = False
		if success:
			votes = db.GqlQuery("SELECT * FROM Vote WHERE proposal = :1 AND creator = :2", proposal, beevote_user)
			vote = votes.get()
			vote.delete()
			time.sleep(0.25)
		votes = db.GqlQuery("SELECT * FROM Vote WHERE proposal = :1", proposal)
		vote_number = votes.count()
		values = {
			'success': success,
			'vote_number': vote_number,
		}
		self.response.out.write(json.dumps(values))

class LoadVotesHandler(webapp2.RequestHandler):
	def get(self):
		group_id = self.request.get('group_id')
		topic_id = self.request.get('topic_id')
		proposal_id = self.request.get('proposal_id')
		proposal_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id), 'Proposal', long(proposal_id))
		proposal = db.get(proposal_key)
		votes_db = db.GqlQuery("SELECT * FROM Vote WHERE proposal = :1", proposal).fetch(20)
		votes = []
		for vote in votes_db:
			votes.append({
				'name': vote.creator.name,
				'surname': vote.creator.surname,
				'email': vote.creator.email,
			})
		values = {
			'success': True,
			'votes': votes,
		}
		self.response.out.write(json.dumps(values))

class OldLoadProposalHandler(webapp2.RequestHandler):
	def get(self):
		group_id = self.request.get('group_id')
		topic_id = self.request.get('topic_id')
		proposal_id = self.request.get('proposal_id')
		proposal_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id), 'Proposal', long(proposal_id))
		proposal = db.get(proposal_key)
		values = {
			'success': True,
			'proposal': {
				'title': proposal.title,
				'description': proposal.description,
				'creator': {
					'name': proposal.creator.name,
					'surname': proposal.creator.surname,
					'email': proposal.creator.email,
				},
				'place': proposal.place,
				'date': str(proposal.date),
				'time': str(proposal.time),
			}
		}
		self.response.out.write(json.dumps(values))

class UpdateUser(webapp2.RequestHandler):
	def post(self):
		name = self.request.get('edit_name', None)
		surname = self.request.get('edit_surname', None)
		language = self.request.get('edit_language', None)
		img = self.request.get('edit_img', None)
		user = users.get_current_user()
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		if name != None and name == "":
			values = {
				'success': False,
				'error': 'Name is required',
			}
		elif  surname != None and surname == "":
			values = {
				'success': False,
				'error': 'Surname is required',
			}
		elif  language != None and language == "":
			values = {
				'success': False,
				'error': 'Language is required',
			}
		elif  img != None and len(img) >= max_image_size:
			values = {
				'success': False,
				'error': 'You cannot upload an image bigger than 850 kb',
			}
		else:
			
			if name != None:
				beevote_user.name = name
			if surname != None:
				beevote_user.surname = surname
			if language != None:
				beevote_user.language = language
			if img:
				beevote_user.img = img
			beevote_user.put()
			user_id = user.user_id()
			values = {
				'success': True,
				'user_id': user_id,
			}
		self.response.out.write(json.dumps(values))
		self.redirect('/home')

class LoadGroupMembersHandler(webapp2.RequestHandler):
	def get(self):
		group_id = self.request.get('group_id')
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		values = {
			'success': True,
			'members': group.members,
		}
		time.sleep(1)
		self.response.out.write(json.dumps(values))

class CreateGroupHandler(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		name = self.request.get('name')
		description = self.request.get('description')
		img = self.request.get('img', None)
		if name == "":
			values = {
				'success': False,
				'error': 'Name is required',
			}
		elif  img != None and len(img) >= max_image_size:
			values = {
				'success': False,
				'error': 'You cannot upload an image bigger than 850 kb',
			}
		else:
			group = models.Group.create(
				name = name,
				creator = beevote_user,
				description = description,
				img = img
			)
			group.put()
			group_id = group.key().id()
			values = {
				'success': True,
				'group_id': group_id,
			}
		self.response.out.write(json.dumps(values))

class UpdateGroupHandler(webapp2.RequestHandler):
	def post(self, group_id):
		user = users.get_current_user()
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		name = self.request.get('name', None)
		description = self.request.get('description', None)
		img = self.request.get('img', None)
		if name != None and name == "":
			values = {
				'success': False,
				'error': 'Name is required',
			}
		elif  img != None and len(img) >= max_image_size:
			values = {
				'success': False,
				'error': 'You cannot upload an image bigger than 850 kb',
			}
		else:
			group_key = db.Key.from_path('Group', long(group_id))
			group = db.get(group_key)
			if name != None and name != group.name:
				group.name = name
				GroupNotification.create(GroupNotification.GROUP_NAME_CHANGE, group, beevote_user)
			if description != None and description != group.description:
				GroupNotification.create(GroupNotification.GROUP_DESCRIPTION_CHANGE, group, beevote_user)
				group.description = description
			if img:
				GroupNotification.create(GroupNotification.GROUP_IMAGE_CHANGE, group, beevote_user)
				group.img = img
			group.put()
			group_id = group.key().id()
			values = {
				'success': True,
				'group_id': group_id,
			}
		self.response.out.write(json.dumps(values))

class CreateTopicHandler(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		group_id = self.request.get('group_id')
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		
		title = self.request.get('title')
		place= self.request.get('place')
		date = self.request.get('date')
		time = self.request.get('time')
		deadline = self.request.get('deadline')
		description = self.request.get('description')
		img = self.request.get('img', None)
		tzoffset = self.request.get('timezoneOffset')
		
		if title == "":
			values = {
				'success': False,
				'error': 'Title is required',
			}
		elif group_id == "":
			values = {
				'success': False,
				'error': 'Group ID is required',
			}
		elif  img != None and len(img) >= max_image_size:
			values = {
				'success': False,
				'error': 'You cannot upload an image bigger than 850 kb',
			}
		else:
			try:
				topic = models.Topic.create(
					title=title,
					group=group,
					creator=beevote_user,
					place=place,
					date=date,
					time=time,
					deadline=deadline,
					description=description,
					img=img
				)
				topic.put()
				models.TopicNotification.create(models.TopicNotification.TOPIC_CREATION, topic=topic)
				group.put()
				values = {
					'success': True,
					'group_id': group_id,
					'topic_id': topic.key().id(),
				}
			except Exception as exc:
				values = {
					'success': False,
					'error': exc.args[0]
				}
		self.response.out.write(json.dumps(values))

class RemoveTopicHandler(webapp2.RequestHandler):
	def post(self, group_id, topic_id):
		user = users.get_current_user()
		user_id = user.user_id()
		beevote_user = models.get_beevote_user_from_google_id(user_id)
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		if not is_user_in_group(beevote_user, group):
			values = {
				'success': False,
				'group_id': group_id,
				'error': "You are not authorized to interact with this group",
			}
		else:
			topic_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id))
			topic = db.get(topic_key)

			if topic.creator.key() == beevote_user.key():
				topic.delete()
				# TODO implement topic removal notification?
				values = {
					'success': True,
					'group_id': group_id,
				}
			else:
				values = {
					'success': False,
					'group_id': group_id,
					'error': "You are not the creator of the topic",
				}
		self.response.out.write(json.dumps(values))


class UpdateTopicHandler(webapp2.RequestHandler):
	def post(self, group_id, topic_id):
		img = self.request.get('img', None)
		topic = models.Topic.get_from_id(long(group_id), long(topic_id))
		if img != None and len(img) >= max_image_size:
			values = {
				'success': False,
				'error': 'You cannot upload an image bigger than 850 kb',
			}
		else:
			if img:
				topic.img = img
				TopicNotification.create(TopicNotification.TOPIC_IMAGE_CHANGE, topic)
			topic.put()
			topic_id = topic.key().id()
			values = {
				'success': True,
				'group_id': topic.group.key().id(),
				'topic_id': topic_id,
			}
		self.response.out.write(json.dumps(values))

class MemberAutocompleteHandler(webapp2.RequestHandler):
	def get(self):
		query = self.request.get('query').lower()
		users = db.GqlQuery("SELECT * FROM BeeVoteUser").fetch(1000)
		users = [u for u in users if (query in u.name.lower()+" "+u.surname.lower())][:10]
		suggestions = []
		for user in users:
			suggestions.append({"value" : user.email, "data" : user.name+" "+user.surname})
		values = {
			"query" : "Unit",
			"suggestions" : suggestions, 
		}
		self.response.out.write(json.dumps(values))

class TopicsNotificationsHandler(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		user_id = user.user_id()
		beevote_user = models.get_beevote_user_from_google_id(user_id)
		all_notifications = models.TopicNotification.get_for_beevote_user(beevote_user, beevote_user.get_topics_by_group_membership())
		
		for group_id in all_notifications.keys():
			for topic_id in all_notifications[group_id].keys():
				notif = {
					'topic_creations': 0,
					'topic_image_change': 0,
					'proposal_creations': 0,
					'topic_expirations': 0,
				}
				for db_notification in all_notifications[group_id][topic_id]:
					if db_notification.notification_code == models.TopicNotification.TOPIC_CREATION:
						notif['topic_creations'] += 1
					elif db_notification.notification_code == models.TopicNotification.TOPIC_IMAGE_CHANGE:
						notif['topic_image_change'] += 1
					elif db_notification.notification_code == models.TopicNotification.PROPOSAL_CREATION:
						notif['proposal_creations'] += 1
					if db_notification.notification_code == models.TopicNotification.TOPIC_EXPIRATION:
						notif['topic_expirations'] += 1
				all_notifications[group_id][topic_id] = notif
		self.response.out.write(json.dumps(all_notifications))

class GroupNotificationsHandler(webapp2.RequestHandler):
	def get(self, group_id):
		user = users.get_current_user()
		user_id = user.user_id()
		beevote_user = models.get_beevote_user_from_google_id(user_id)
		group = models.Group.get_from_id(group_id)
		notifications = group.get_notifications_for_user(beevote_user)
		
		group_notif = {
			'group_invitations': 0,
			'group_name_changes': 0,
			'group_description_changes': 0,
			'group_image_changes': 0,
		}
		for db_notification in notifications['group_notifications']:
			if db_notification.notification_code == models.GroupNotification.GROUP_INVITATION:
				group_notif['group_invitations'] += 1
			elif db_notification.notification_code == models.GroupNotification.GROUP_NAME_CHANGE:
				group_notif['group_name_changes'] += 1
			elif db_notification.notification_code == models.GroupNotification.GROUP_DESCRIPTION_CHANGE:
				group_notif['group_description_changes'] += 1
			elif db_notification.notification_code == models.GroupNotification.GROUP_IMAGE_CHANGE:
				group_notif['group_image_changes'] += 1
		notifications['group_notifications'] = group_notif
		
		for topic_id in notifications['topics_notifications']:
			notif = {
				'topic_creations': 0,
				'topic_image_changes': 0,
				'proposal_creations': 0,
				'topic_expirations': 0,
			}
			for db_notification in notifications['topics_notifications'][topic_id]:
				if db_notification.notification_code == models.TopicNotification.TOPIC_CREATION:
					notif['topic_creations'] += 1
				elif db_notification.notification_code == models.TopicNotification.TOPIC_IMAGE_CHANGE:
					notif['topic_image_changes'] += 1
				elif db_notification.notification_code == models.TopicNotification.PROPOSAL_CREATION:
					notif['proposal_creations'] += 1
				elif db_notification.notification_code == models.TopicNotification.TOPIC_EXPIRATION:
					notif['topic_expirations'] += 1
			notifications['topics_notifications'][topic_id] = notif
		
		self.response.out.write(json.dumps(notifications))

class RemoveGroupHandler(webapp2.RequestHandler):
	def post(self, group_id):
		user = users.get_current_user()
		user_id = user.user_id()
		beevote_user = models.get_beevote_user_from_google_id(user_id)
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		if not is_user_in_group(beevote_user, group):
			values = {
				'success': False,
				'group_id': group_id,
				'error': "You are not authorized to interact with this group",
			}
		else:
			if beevote_user.key() in group.admins:
				group.delete()
				values = {
					'success': True,
				}
			else:
				values = {
					'success': False,
					'group_id': group_id,
					'error': "You are not an admin of the group",
				}
		self.response.out.write(json.dumps(values))

class AddGroupMemberHandler(webapp2.RequestHandler):
	def post(self, group_id):
		user = users.get_current_user()
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		if not is_user_in_group(models.get_beevote_user_from_google_id(user.user_id()), group):
			values = {
				'success': False,
				'group_id': group_id,
				'error': "You are not authorized to interact with this group",
			}
		else:
			email = self.request.get("email")
			beevote_user = db.GqlQuery('SELECT * FROM BeeVoteUser WHERE email = :1', email).get()
			if beevote_user:
				beevote_user_key = beevote_user.key()
				if beevote_user_key not in group.members:
					group.members.append(beevote_user_key)
					models.GroupNotification.create(models.GroupNotification.GROUP_INVITATION, group, beevote_user=beevote_user)
					group.put()
					values = {
						'success': True,
						'group_id': group_id
					}
				else:
					values = {
						'success': False,
						'group_id': group_id,
						'error': "User associated to email '"+email+"' is already in the group",
					}
			else:
				values = {
					'success': False,
					'error': "Email '"+email+"' is not associated to any BeeVote account",
				}
		self.response.out.write(json.dumps(values))

class RemoveGroupMemberHandler(webapp2.RequestHandler):
	def post(self, group_id):
		user = users.get_current_user()
		current_beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		if not is_user_in_group(current_beevote_user, group):
			values = {
				'success': False,
				'group_id': group_id,
				'error': "You are not authorized to interact with this group",
			}
		else:
			email = self.request.get("email")
			deleted_beevote_user = db.GqlQuery('SELECT * FROM BeeVoteUser WHERE email = :1', email).get()
			group_key = db.Key.from_path('Group', long(group_id))
			group = db.get(group_key)
			deleted_user_key = deleted_beevote_user.key()
			if deleted_user_key not in group.members:
				values = {
					'success': False,
					'group_id': group_id,
					'error': "User associated to email '"+email+"' is not in the group",
				}
			else:
				group.members.remove(deleted_user_key)
				if deleted_user_key in group.admins:
					group.admins.remove(deleted_user_key)
				# TODO implement notification when a user leaves a group?
				group.put()
				values = {
					'success': True,
					'group_id': group_id,
				}
		self.response.out.write(json.dumps(values))

class CreateProposalHandler(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		title = self.request.get('title')
		where = self.request.get('place')
		date = self.request.get('date')
		time = self.request.get('time')
		description = self.request.get('description')
		topic_id = self.request.get('topic_id')
		group_id = self.request.get('group_id')
		if title == "":
			values = {
				'success': False,
				'error': 'Title is required',
			}
		elif group_id == "":
			values = {
				'success': False,
				'error': 'Group ID is required',
			}
		elif topic_id == "":
			values = {
				'success': False,
				'error': 'Topic ID is required',
			}
		else:
			try:
				topic = models.Topic.get_from_id(group_id, topic_id)
				proposal = models.Proposal(
					title=title,
					topic=topic,
					parent=topic,
					creator=beevote_user,
				)
				if where != "":
					proposal.place = where
				if date != "":
					proposal.date = datetime.datetime.strptime(date, "%d/%m/%Y").date()
					if proposal.date.year <= 1900:
						raise Exception('Year cannot be before 1900')
				if time != "":
					proposal.time = datetime.datetime.strptime(time, '%H:%M').time()
				proposal.description = description
				proposal.put()
				models.TopicNotification.create(models.TopicNotification.PROPOSAL_CREATION, topic)
				topic.put()
				values = {
					'success': True,
					'group_id': group_id,
					'topic_id': topic_id,
					'proposal_id': proposal.key().id(),
				}
			except Exception as exc:
				values = {
					'success': False,
					'error': exc.args[0]
				}
		self.response.out.write(json.dumps(values))

class RemoveProposalHandler(webapp2.RequestHandler):
	def post(self, group_id, topic_id, proposal_id):
		user = users.get_current_user()
		user_id = user.user_id()
		beevote_user = models.get_beevote_user_from_google_id(user_id)
		group = models.Group.get_from_id(group_id)
		if not is_user_in_group(beevote_user, group):
			values = {
				'success': False,
				'group_id': group_id,
				'error': "You are not authorized to interact with this group",
			}
		else:
			proposal = models.Proposal.get_from_id(group_id, topic_id, proposal_id)
			if proposal.creator.key() == beevote_user.key():
				proposal.delete()
				values = {
					'success': True,
					'group_id': group_id,
					'topic_id': topic_id,
				}
			else:
				values = {
					'success': False,
					'error': "You are not the creator of the proposal",
				}
		self.response.out.write(json.dumps(values))

class RemoveParticipationHandler(webapp2.RequestHandler):
	def post(self, group_id, topic_id):
		user = users.get_current_user()
		user_id = user.user_id()
		beevote_user = models.get_beevote_user_from_google_id(user_id)
		topic = models.Topic.get_from_id(long(group_id), long(topic_id))
		if not is_user_in_group(beevote_user, topic.group):
			values = {
				'success': False,
				'group_id': group_id,
				'topic_id': topic_id,
				'error': "You are not authorized to interact with this group",
			}
		else:
			topic.non_participant_users.append(beevote_user.key())
			topic.put()
			proposals = topic.get_proposals()
			for proposal in proposals:
				votes = db.GqlQuery("SELECT * FROM Vote WHERE proposal = :1 AND creator = :2", proposal, beevote_user)
				for vote in votes:
					vote.delete()
			time.sleep(0.25)
			values = {
				'success': True,
				'group_id': group_id,
				'topic_id': topic_id,
			}
		self.response.out.write(json.dumps(values))

class AddParticipationHandler(webapp2.RequestHandler):
	def post(self, group_id, topic_id):
		user = users.get_current_user()
		user_id = user.user_id()
		beevote_user = models.get_beevote_user_from_google_id(user_id)
		topic = models.Topic.get_from_id(long(group_id), long(topic_id))
		if not is_user_in_group(beevote_user, topic.group):
			values = {
				'success': False,
				'group_id': group_id,
				'topic_id': topic_id,
				'error': "You are not authorized to interact with this group",
			}
		else:
			topic.non_participant_users.remove(beevote_user.key())
			topic.put()
			time.sleep(0.25)
			values = {
				'success': True,
				'group_id': group_id,
				'topic_id': topic_id,
			}
		self.response.out.write(json.dumps(values))

class CreateBugReportHandler(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		
		device = self.request.get('device')
		browser = self.request.get('browser')
		description = self.request.get('description')
		occurrence = self.request.get('occurrence')

		try:
			report = models.BugReport(
				device = device,
				browser = browser,
				description = description,
				creator = beevote_user 
			)
			if occurrence != "":
				report.occurrence = datetime.datetime.strptime(occurrence, "%d/%m/%Y").date()
				if report.occurrence.year <= 1900:
					raise Exception('Year cannot be before 1900')
			report.put()
			mail.send_mail_to_admins(
					sender="BeeVote Bug Report <bug-report@beevote.appspotmail.com>",
					subject="BeeVote bog report received",
					body="""
Dear BeeVote admin,

Your application has received the following bug report:
- ID: {report.key.id}
- Device: {report.device}
- Browser: {report.browser}
- Description: {report.description}
- Occurrence: {report.occurrence}
- Creation: {report.creation}
- Creator ID: {report.creator}

Follow this link to see all bug reports:
{link}

The BeeVote Team
        """.format(report=report, link=self.request.host+"/admin/bug-reports"))
			report_id = report.key().id()
			values = {
				'success': True,
				'report_id': report_id,
			}
		except Exception as exc:
			values = {
				'success': False,
				'error': exc.args[0]
			}
		self.response.out.write(json.dumps(values))

class LogoutHandler(webapp2.RequestHandler):
	def get(self):
		self.redirect(users.create_logout_url('/'))

# End of handlers