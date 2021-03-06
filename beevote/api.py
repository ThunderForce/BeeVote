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

import collections
import datetime
import json
import logging
import time
import traceback

from google.appengine.api import users, memcache
import webapp2

import base_handlers
import constants
import emailer
import language
import models


# Start of functions
def get_json(json_obj):
	return json.dumps(json_obj, indent=4, separators=(',', ': '))

def fetch_user(beevote_user, arguments):
	if beevote_user is None:
		return None
	user = collections.OrderedDict([
		('data', collections.OrderedDict([
			('id', beevote_user.key.id()),
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
			('id', group.key.id()),
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
			('id', topic.key.id()),
			('title', topic.title),
			('description', topic.description),
			('has_image', topic.img != None),
			('place', topic.place if topic.place != "" else None),
			('date', str(topic.date) if topic.date else None),
			('time', str(topic.time) if topic.time else None),
			('deadline', str(topic.deadline) if topic.deadline else None),
			('creator', topic.creator.id()),
			('group_id', topic.group.id())
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
		('id', proposal.key.id()),
		('title', proposal.title),
		('description', proposal.description),
		('creator', fetch_user(proposal.creator.get(), arguments))
	])
	if 'fetch_votes' in arguments and arguments['fetch_votes']:
		votes = proposal.get_votes()
		proposal_dict['vote_number'] = len(votes)
		proposal_dict['votes'] = fetch_votes(votes, arguments)
	if 'fetch_comments' in arguments and arguments['fetch_comments']:
		comments = proposal.get_comments()
		proposal_dict['comment_number'] = len(comments)
		proposal_dict['comments'] = fetch_comments(comments, arguments)
	return proposal_dict

def fetch_groups(groups, arguments):
	groups_ret = []
	for datastore_group in groups:
		group = fetch_group(datastore_group, arguments)
		groups_ret.append(group)
	return groups_ret

def fetch_members_from_group(group, arguments):
	datastore_members = group.get_members()
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

def fetch_comments(comments, arguments):
	comments_ret = []
	for datastore_comment in comments:
		comment = fetch_comment(datastore_comment, arguments)
		comments_ret.append(comment)
	return comments_ret

def fetch_vote(vote, arguments):
	vote_dict = collections.OrderedDict([
		('creator', fetch_user(vote.creator.get(), arguments))
	])
	return vote_dict

def fetch_comment(comment, arguments):
	comment_dict = collections.OrderedDict([
		('creator', fetch_user(comment.creator.get(), arguments)),
		('creation', comment.creation.strftime(constants.comment_date_format)),
		('description', comment.description)
	])
	return comment_dict

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

class LoadGroupsHandler(base_handlers.BaseApiHandler):
	def get(self):
		datastore_groups = self.beevote_user.get_groups_by_membership()
		arguments = {
			'fetch_group_members': self.request.get('fetch_group_members', 'false') == 'true',
			'fetch_topics': self.request.get('fetch_topics', 'false') == 'true',
			'evaluate_deadlines': self.request.get('evaluate_deadlines', 'false') == 'true',
			'fetch_proposals': self.request.get('fetch_proposals', 'false') == 'true',
		}
		groups = fetch_groups(datastore_groups, arguments)
		
		self.response.out.write(get_json(groups))

class LoadGroupHandler(base_handlers.BaseApiHandler):
	def get(self, group_id):
		group = models.Group.get_from_id(group_id)
		if (not group):
			self.abort(404, detail="This group does not exist.")
		'''
		if not group.contains_user(models.BeeVoteUser.get_from_google_id(user.user_id())):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		'''
		arguments = {
			'fetch_group_members': self.request.get('fetch_group_members', 'false') == 'true',
			'fetch_topics': self.request.get('fetch_topics', 'false') == 'true',
			'evaluate_deadlines': self.request.get('evaluate_deadlines', 'false') == 'true',
			'fetch_proposals': self.request.get('fetch_proposals', 'false') == 'true',
		}
		
		group_json = fetch_group(group, arguments)
		models.GroupAccess.update_specific_access(group, self.beevote_user)
		self.response.out.write(get_json(group_json))

class LoadTopicHandler(base_handlers.BaseApiHandler):
	def get(self, group_id, topic_id):
		group = models.Group.get_from_id(group_id)
		if (not group):
			self.abort(404, detail="This group does not exist.")
		'''
		if not group.contains_user(models.BeeVoteUser.get_from_google_id(user.user_id())):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		'''
		arguments = {
			'evaluate_deadlines': self.request.get('evaluate_deadlines', 'false') == 'true',
			'fetch_proposals': self.request.get('fetch_proposals', 'false') == 'true',
			'fetch_votes': self.request.get('fetch_votes', 'false') == 'true',
		}
		
		topic = models.Topic.get_from_id(group_id, topic_id)
		topic_json = fetch_topic(topic, arguments)
		models.TopicAccess.update_specific_access(topic, self.beevote_user)
		self.response.out.write(get_json(topic_json))

class LoadProposalHandler(base_handlers.BaseApiHandler):
	def get(self, group_id, topic_id, proposal_id):
		group = models.Group.get_from_id(group_id)
		if (not group):
			self.abort(404, detail="This group does not exist.")
		'''
		if not group.contains_user(models.BeeVoteUser.get_from_google_id(user.user_id())):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		'''
		arguments = {
			'fetch_votes': self.request.get('fetch_votes', 'false') == 'true',
			'fetch_users': self.request.get('fetch_users', 'false') == 'true',
			'fetch_comments': self.request.get('fetch_comments', 'false') == 'true',
		}
		
		proposal = models.Proposal.get_from_id(group_id, topic_id, proposal_id)
		proposal_json = fetch_proposal(proposal, arguments)
		
		self.response.out.write(get_json(proposal_json))

class LoadParticipantsHandler(base_handlers.BaseApiHandler):
	def get(self, group_id, topic_id):
		group = models.Group.get_from_id(group_id)
		if (not group):
			self.abort(404, detail="This group does not exist.")
		'''
		if not group.contains_user(models.BeeVoteUser.get_from_google_id(user.user_id())):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		'''
		topic = models.Topic.get_from_id(group_id, topic_id)

		arguments = {
			'fetch_users': self.request.get('fetch_users', 'false') == 'true',
		}

		participants = [part for part in group.members if part not in topic.non_participant_users]
		
		beevote_users = models.BeeVoteUser.get_from_keys(participants)
		json_users = []
		for user in beevote_users:
			json_users.append(fetch_user(user, arguments))
		
		self.response.out.write(get_json(json_users))


class LoadUserHandler(base_handlers.BaseApiHandler):
	def get(self, user_id):
		target_beevote_user = models.BeeVoteUser.get_from_id(user_id)
		
		arguments = {
			'is_current_user': target_beevote_user.key == self.beevote_user.key
		}
		
		beevote_user_ret = fetch_user(target_beevote_user, arguments)
		
		self.response.out.write(get_json(beevote_user_ret))

class CreateVoteHandler(base_handlers.BaseApiHandler):
	def post(self):
		group_id = self.request.get('group_id')
		topic_id = self.request.get('topic_id')
		proposal_id = self.request.get('proposal_id')
		proposal = models.Proposal.get_from_id(long(group_id), long(topic_id), long(proposal_id))
		success = True
		if proposal.topic.get().deadline != None:
			currentdatetime = datetime.datetime.now()
			proposal.topic.get().expired = proposal.topic.get().deadline < currentdatetime
			if proposal.topic.get().expired:
				success = False
		if success:
			vote = models.Vote(
				proposal = proposal.key,
				parent = proposal.key,
				creator = self.beevote_user.key
			)
			vote.put()
			time.sleep(0.25)		
		votes = proposal.get_votes()
		vote_number = len(votes)
		values = {
			'success': success,
			'vote_number': vote_number
		}
		self.response.out.write(json.dumps(values))

class RemoveVoteHandler(base_handlers.BaseApiHandler):
	def post(self):
		group_id = self.request.get('group_id')
		topic_id = self.request.get('topic_id')
		proposal_id = self.request.get('proposal_id')
		proposal = models.Proposal.get_from_id(long(group_id), long(topic_id), long(proposal_id))
		success = True
		if proposal.topic.get().deadline != None:
			currentdatetime = datetime.datetime.now()
			proposal.topic.get().expired = proposal.topic.get().deadline < currentdatetime
			if proposal.topic.get().expired:
				success = False
		if success:
			proposal.remove_user_vote(self.beevote_user)
			time.sleep(0.25)
		votes = proposal.get_votes()
		vote_number = len(votes)
		values = {
			'success': success,
			'vote_number': vote_number,
		}
		self.response.out.write(json.dumps(values))

class LoadVotesHandler(base_handlers.BaseApiHandler):
	def get(self):
		group_id = self.request.get('group_id')
		topic_id = self.request.get('topic_id')
		proposal_id = self.request.get('proposal_id')
		proposal = models.Proposal.get_from_id(long(group_id), long(topic_id), long(proposal_id))
		votes_db = proposal.get_votes()
		votes = []
		for vote in votes_db:
			votes.append({
				'name': vote.creator.get().name,
				'surname': vote.creator.get().surname,
				'email': vote.creator.get().email,
			})
		values = {
			'success': True,
			'votes': votes,
		}
		self.response.out.write(json.dumps(values))

class OldLoadProposalHandler(base_handlers.BaseApiHandler):
	def get(self):
		group_id = self.request.get('group_id')
		topic_id = self.request.get('topic_id')
		proposal_id = self.request.get('proposal_id')
		proposal = models.Proposal.get_from_id(long(group_id), long(topic_id), long(proposal_id))
		topic = proposal.topic.get()
		values = {
			'success': True,
			'proposal': {
				'title': proposal.title,
				'description': proposal.description,
			}
		}
		if proposal.creator.get():
			values['proposal']['creator'] = {
				'name': proposal.creator.get().name,
				'surname': proposal.creator.get().surname,
				'email': proposal.creator.get().email,
			}
		else:
			values['proposal']['creator'] = None
		if topic.place == "" and proposal.place:
			values['proposal']['place'] = proposal.place
		if topic.date == None and proposal.date:
			values['proposal']['date'] = str(proposal.date)
		if topic.time == None and proposal.time:
			values['proposal']['time'] = str(proposal.time)
		self.response.out.write(json.dumps(values))

class UpdateUser(base_handlers.BaseApiHandler):
	def post(self):
		name = self.request.get('edit_name', None)
		surname = self.request.get('edit_surname', None)
		language = self.request.get('edit_language', None)
		img = self.request.get('edit_img', None)
		if name != None and name == "":
			values = {
				'success': False,
				'error': self.lang['errors']['name_required'],
			}
		elif surname != None and surname == "":
			values = {
				'success': False,
				'error': self.lang['errors']['surname_required'],
			}
		elif img != None and len(img) >= constants.max_image_size:
			values = {
				'success': False,
				'error': self.lang['errors']['image_too_big'],
			}
		else:
			
			if name != None:
				self.beevote_user.name = name
			if surname != None:
				self.beevote_user.surname = surname
			if language != None:
				self.beevote_user.language = language
			if img:
				self.beevote_user.img = img
			self.beevote_user.put()
			user_id = self.beevote_user.key.id()
			values = {
				'success': True,
				'user_id': user_id,
			}
		self.response.out.write(json.dumps(values))

class LoadGroupMembersHandler(base_handlers.BaseApiHandler):
	def get(self):
		group_id = self.request.get('group_id')
		group = models.Group.get_from_id(long(group_id))
		values = {
			'success': True,
			'members': group.get_members(),
		}
		time.sleep(1)
		self.response.out.write(json.dumps(values))

class CreateGroupHandler(base_handlers.BaseApiHandler):
	def post(self):
		name = self.request.get('name')
		description = self.request.get('description')
		img = self.request.get('img', None)
		if name == "":
			values = {
				'success': False,
				'error': self.lang['errors']['name_required'],
			}
		elif img != None and len(img) >= constants.max_image_size:
			values = {
				'success': False,
				'error': self.lang['errors']['image_too_big'],
			}
		else:
			group = models.Group.create(
				name = name,
				creator_key = self.beevote_user.key,
				description = description,
				img = img
			)
			group.put()
			group_id = group.key.id()
			values = {
				'success': True,
				'group_id': group_id,
			}
		self.response.out.write(json.dumps(values))

class UpdateGroupHandler(base_handlers.BaseApiHandler):
	def post(self, group_id):
		name = self.request.get('name', None)
		description = self.request.get('description', None)
		img = self.request.get('img', None)
		if name != None and name == "":
			values = {
				'success': False,
				'error': self.lang['errors']['name_required'],
			}
		elif img != None and len(img) >= constants.max_image_size:
			values = {
				'success': False,
				'error': self.lang['errors']['image_too_big'],
			}
		else:
			group = models.Group.get_from_id(long(group_id))
			if name != None and name != group.name:
				group.name = name
				models.GroupNotification.create(models.GroupNotification.GROUP_NAME_CHANGE, group.key, self.beevote_user.key)
			if description != None and description != group.description:
				models.GroupNotification.create(models.GroupNotification.GROUP_DESCRIPTION_CHANGE, group.key, self.beevote_user.key)
				group.description = description
			if img:
				models.GroupNotification.create(models.GroupNotification.GROUP_IMAGE_CHANGE, group.key, self.beevote_user.key)
				group.img = img
			group.put()
			models.GroupAccess.update_specific_access(group, self.beevote_user)
			group_id = group.key.id()
			values = {
				'success': True,
				'group_id': group_id,
			}
		self.response.out.write(json.dumps(values))

class CreateTopicHandler(base_handlers.BaseApiHandler):
	def post(self):
		group_id = self.request.get('group_id')
		group = models.Group.get_from_id(long(group_id))
		
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
				'error': self.lang['errors']['title_required'],
			}
		elif group_id == "":
			values = {
				'success': False,
				'error': self.lang['errors']['group_id_required'],
			}
		elif img != None and len(img) >= constants.max_image_size:
			values = {
				'success': False,
				'error': self.lang['errors']['image_too_big'],
			}
		else:
			try:
				topic = models.Topic.create(
					title=title,
					group_key=group.key,
					creator_key=self.beevote_user.key,
					place=place,
					date=date,
					time=time,
					deadline=deadline,
					description=description,
					img=img
				)
				topic.put()
				models.TopicNotification.create(models.TopicNotification.TOPIC_CREATION, topic_key=topic.key)
				models.TopicAccess.update_specific_access(topic, self.beevote_user)
				group.put()
				emailed_users = [u for u in group.get_members() if u.key != self.beevote_user.key and models.GroupPersonalSettings.get_settings(u, group).topic_creation_email]
				for user in emailed_users:
					if not user.language:
						lang_package= 'en'
					else:
						lang_package = user.language
					emailer.send_topic_creation_email(user, lang_package, topic, self.request.host+"/group/"+str(group.key.id())+"/topic/"+str(topic.key.id()))
				values = {
					'success': True,
					'group_id': group_id,
					'topic_id': topic.key.id(),
				}
			except Exception as exc:
				stacktrace = traceback.format_exc()
				logging.error("%s", stacktrace)
				values = {
					'success': False,
					'error': exc.args[0]
				}
		self.response.out.write(json.dumps(values))

class RemoveTopicHandler(base_handlers.BaseApiHandler):
	def post(self, group_id, topic_id):
		group = models.Group.get_from_id(long(group_id))
		if not group.contains_user(self.beevote_user):
			values = {
				'success': False,
				'group_id': group_id,
				'error': self.lang['errors']['group_authorization_denied'],
			}
		else:
			topic = models.Topic.get_from_id(long(group_id), long(topic_id))

			if topic.creator == self.beevote_user.key:
				topic.key.delete()
				# TODO implement topic removal notification?
				values = {
					'success': True,
					'group_id': group_id,
				}
			else:
				values = {
					'success': False,
					'group_id': group_id,
					'error': self.lang['errors']['topic_authorization_denied'],
				}
		self.response.out.write(json.dumps(values))


class UpdateTopicHandler(base_handlers.BaseApiHandler):
	def post(self, group_id, topic_id):
		img = self.request.get('img', None)
		topic = models.Topic.get_from_id(long(group_id), long(topic_id))
		if img != None and len(img) >= constants.max_image_size:
			values = {
				'success': False,
				'error': self.lang['errors']['image_too_big'],
			}
		else:
			if img:
				topic.img = img
				models.TopicNotification.create(models.TopicNotification.TOPIC_IMAGE_CHANGE, topic_key=topic.key)
			topic.put()
			models.TopicAccess.update_specific_access(topic, self.beevote_user)
			topic_id = topic.key.id()
			values = {
				'success': True,
				'group_id': topic.group.id(),
				'topic_id': topic_id,
			}
		self.response.out.write(json.dumps(values))

class MemberAutocompleteHandler(base_handlers.BaseApiHandler):
	def get(self):
		query = self.request.get('query').lower()
		users = models.BeeVoteUser.get_all()
		users = [u for u in users if (query in u.name.lower()+" "+u.surname.lower())][:10]
		suggestions = []
		for user in users:
			suggestions.append({"value" : user.email, "data" : user.name+" "+user.surname})
		values = {
			"query" : "Unit",
			"suggestions" : suggestions, 
		}
		self.response.out.write(json.dumps(values))

class TopicsNotificationsHandler(base_handlers.BaseApiHandler):
	def get(self):
		all_notifications = memcache.get('topics_notifications_by_beevote_user_%s' % self.beevote_user.key.id()) # @UndefinedVariable
		if not all_notifications:
			topics = self.beevote_user.get_topics_by_group_membership()
			all_notifications = models.TopicNotification.get_for_beevote_user(self.beevote_user, topics)
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
			memcache.add('topics_notifications_by_beevote_user_%s' % self.beevote_user.key.id(), all_notifications, time=10) # @UndefinedVariable
		self.response.out.write(json.dumps(all_notifications))

class GroupNotificationsHandler(base_handlers.BaseApiHandler):
	def get(self, group_id):
		group = models.Group.get_from_id(group_id)
		notifications = group.get_notifications_for_user(self.beevote_user)
		
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

class TopicNotificationsHandler(base_handlers.BaseApiHandler):
	def get(self, group_id, topic_id):
		topic = models.Topic.get_from_id(group_id, topic_id)
		notifications = topic.get_notifications_for_user(self.beevote_user)
		
		notif = {
			'topic_creations': 0,
			'topic_image_changes': 0,
			'proposal_creations': 0,
			'topic_expirations': 0,
		}
		for db_notification in notifications:
			if db_notification.notification_code == models.TopicNotification.TOPIC_CREATION:
				notif['topic_creations'] += 1
			elif db_notification.notification_code == models.TopicNotification.TOPIC_IMAGE_CHANGE:
				notif['topic_image_changes'] += 1
			elif db_notification.notification_code == models.TopicNotification.PROPOSAL_CREATION:
				notif['proposal_creations'] += 1
			elif db_notification.notification_code == models.TopicNotification.TOPIC_EXPIRATION:
				notif['topic_expirations'] += 1
		notifications = notif
		
		self.response.out.write(json.dumps(notifications))

class RemoveGroupHandler(base_handlers.BaseApiHandler):
	def post(self, group_id):
		group = models.Group.get_from_id(long(group_id))
		if not group.contains_user(self.beevote_user):
			values = {
				'success': False,
				'group_id': group_id,
				'error': self.lang['errors']['group_authorization_denied'],
			}
		else:
			if self.beevote_user.key in group.admins:
				group.key.delete()
				values = {
					'success': True,
				}
			else:
				values = {
					'success': False,
					'group_id': group_id,
					'error': self.lang['errors']['group_admin_authorization_denied'],
				}
		self.response.out.write(json.dumps(values))

class AddGroupMemberHandler(base_handlers.BaseApiHandler):
	def post(self, group_id):
		group = models.Group.get_from_id(long(group_id))
		if not group.contains_user(self.beevote_user):
			values = {
				'success': False,
				'group_id': group_id,
				'error': self.lang['errors']['group_authorization_denied'],
			}
		else:
			email = self.request.get("email")
			beevote_user = models.BeeVoteUser.get_by_email(email)
			if beevote_user:
				beevote_user_key = beevote_user.key
				if beevote_user_key not in group.members:
					group.members.append(beevote_user_key)
					models.GroupNotification.create(models.GroupNotification.GROUP_INVITATION, group.key, beevote_user_key=beevote_user.key)
					group.put()
					models.GroupAccess.update_specific_access(group, self.beevote_user)
					values = {
						'success': True,
						'group_id': group_id
					}
				else:
					values = {
						'success': False,
						'group_id': group_id,
						'error': self.lang['errors']['email_already_in_the_group'].format(email=email),
					}
			else:
				values = {
					'success': False,
					'error': self.lang['errors']['email_not_registered'].format(email=email),
				}
		self.response.out.write(json.dumps(values))

class RemoveGroupMemberHandler(base_handlers.BaseApiHandler):
	def post(self, group_id):
		group = models.Group.get_from_id(long(group_id))
		if not group.contains_user(self.beevote_user):
			values = {
				'success': False,
				'group_id': group_id,
				'error': self.lang['errors']['group_authorization_denied'],
			}
		else:
			email = self.request.get("email")
			deleted_beevote_user = models.BeeVoteUser.get_by_email(email)
			group = models.Group.get_from_id(long(group_id))
			deleted_user_key = deleted_beevote_user.key
			if deleted_user_key not in group.members:
				values = {
					'success': False,
					'group_id': group_id,
					'error': self.lang['errors']['email_not_in_the_group'].format(email=email),
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

class CreateProposalHandler(base_handlers.BaseApiHandler):
	def post(self):
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
				'error': self.lang['errors']['title_required'],
			}
		elif group_id == "":
			values = {
				'success': False,
				'error': self.lang['errors']['group_id_required'],
			}
		elif topic_id == "":
			values = {
				'success': False,
				'error': self.lang['errors']['topic_id_required'],
			}
		else:
			try:
				topic = models.Topic.get_from_id(group_id, topic_id)
				proposal = models.Proposal(
					title=title,
					topic=topic.key,
					parent=topic.key,
					creator=self.beevote_user.key,
				)
				if where != "" and topic.place == "":
					proposal.place = where
				if date != "" and topic.date is None:
					proposal.date = datetime.datetime.strptime(date, constants.proposal_input_date_format).date()
					if proposal.date.year <= 1900:
						raise Exception(self.lang['errors']['year_before_1900'])
				if time != "" and topic.time is None:
					proposal.time = datetime.datetime.strptime(time, constants.proposal_input_time_format).time()
				proposal.description = description
				proposal.put()
				models.TopicNotification.create(models.TopicNotification.PROPOSAL_CREATION, topic_key=topic.key)
				models.TopicAccess.update_specific_access(topic, self.beevote_user)
				topic.put()
				emailed_users = [u for u in topic.group.get().get_members() if u.key != self.beevote_user.key and models.TopicPersonalSettings.get_settings(u, topic).proposal_creation_email]
				
				for user in emailed_users:
					if not user.language:
						lang_package= 'en'
					else:
						lang_package = user.language
					emailer.send_proposal_creation_email(user, lang_package, proposal, self.request.host+"/group/"+str(topic.group.id())+"/topic/"+str(topic.key.id()))
				values = {
					'success': True,
					'group_id': group_id,
					'topic_id': topic_id,
					'proposal_id': proposal.key.id(),
				}
			except Exception as exc:
				stacktrace = traceback.format_exc()
				logging.error("%s", stacktrace)
				values = {
					'success': False,
					'error': exc.args[0]
				}
		self.response.out.write(json.dumps(values))

class CreateProposalCommentHandler(base_handlers.BaseApiHandler):
	def post(self, group_id, topic_id, proposal_id):
		description = self.request.get('comment')
		if description == "":
			values = {
				'success': False,
				'error': self.lang['errors']['comment_empty'],
			}
		else:
			try:
				proposal = models.Proposal.get_from_id(group_id, topic_id, proposal_id)
				comment = models.ProposalComment(
					description=description,
					proposal=proposal.key,
					parent=proposal.key,
					creator=self.beevote_user.key,
				)
				comment.put()
				# TODO: manage notifications
				values = {
					'success': True,
					'group_id': group_id,
					'topic_id': topic_id,
					'proposal_id': proposal_id,
					'comment_id': comment.key.id(),
					'comment_creator': fetch_user(comment.creator.get(), []),
					'comment_creation': comment.creation.strftime(constants.comment_date_format),
					'comment_description': comment.description
				}
			except Exception as exc:
				stacktrace = traceback.format_exc()
				logging.error("%s", stacktrace)
				values = {
					'success': False,
					'error': exc.args[0]
				}
		self.response.out.write(json.dumps(values))

class RemoveProposalHandler(base_handlers.BaseApiHandler):
	def post(self, group_id, topic_id, proposal_id):
		group = models.Group.get_from_id(group_id)
		if not group.contains_user(self.beevote_user):
			values = {
				'success': False,
				'group_id': group_id,
				'error': self.lang['errors']['group_authorization_denied'],
			}
		else:
			proposal = models.Proposal.get_from_id(group_id, topic_id, proposal_id)
			if proposal.creator == self.beevote_user.key:
				proposal.key.delete()
				values = {
					'success': True,
					'group_id': group_id,
					'topic_id': topic_id,
				}
			else:
				values = {
					'success': False,
					'error': self.lang['errors']['proposal_authorization_denied'],
				}
		self.response.out.write(json.dumps(values))

class RemoveParticipationHandler(base_handlers.BaseApiHandler):
	def post(self, group_id, topic_id):
		topic = models.Topic.get_from_id(long(group_id), long(topic_id))
		if not topic.group.get().contains_user(self.beevote_user):
			values = {
				'success': False,
				'group_id': group_id,
				'topic_id': topic_id,
				'error': self.lang['errors']['group_authorization_denied'],
			}
		else:
			topic.non_participant_users.append(self.beevote_user.key)
			topic.put()
			topic.delete_votes_by_user(self.beevote_user)
			time.sleep(0.25)
			values = {
				'success': True,
				'group_id': group_id,
				'topic_id': topic_id,
			}
		self.response.out.write(json.dumps(values))

class AddParticipationHandler(base_handlers.BaseApiHandler):
	def post(self, group_id, topic_id):
		topic = models.Topic.get_from_id(long(group_id), long(topic_id))
		if not topic.group.get().contains_user(self.beevote_user):
			values = {
				'success': False,
				'group_id': group_id,
				'topic_id': topic_id,
				'error': self.lang['errors']['group_authorization_denied'],
			}
		else:
			topic.non_participant_users.remove(self.beevote_user.key)
			topic.put()
			time.sleep(0.25)
			values = {
				'success': True,
				'group_id': group_id,
				'topic_id': topic_id,
			}
		self.response.out.write(json.dumps(values))

class UpdateGroupPersonalSettingsHandler(base_handlers.BaseApiHandler):
	def post(self, group_id):
		topic_creation_email = self.request.get("topic_creation_email", None)
		group = models.Group.get_from_id(group_id)
		personal_settings = models.GroupPersonalSettings.get_settings(self.beevote_user, group)
		if topic_creation_email:
			personal_settings.topic_creation_email = (topic_creation_email is not None)
		personal_settings.put()
		values = {
			'success': True,
			'group_id': group_id,
		}
		self.response.out.write(json.dumps(values))

class UpdateTopicPersonalSettingsHandler(base_handlers.BaseApiHandler):
	def post(self, group_id, topic_id):
		proposal_creation_email = self.request.get("proposal_creation_email", None)
		topic = models.Topic.get_from_id(group_id, topic_id)
		personal_settings = models.TopicPersonalSettings.get_settings(self.beevote_user, topic)
		if proposal_creation_email:
			personal_settings.proposal_creation_email = (proposal_creation_email is not None)
		personal_settings.put()
		values = {
			'success': True,
			'group_id': group_id,
			'topic_id': topic_id,
		}
		self.response.out.write(json.dumps(values))

class CreateBugReportHandler(base_handlers.BaseApiHandler):
	def post(self):
		device = self.request.get('device')
		browser = self.request.get('browser')
		description = self.request.get('description')
		occurrence = self.request.get('occurrence')

		try:
			report = models.BugReport(
				device = device,
				browser = browser,
				description = description,
				creator = self.beevote_user.key,
			)
			if occurrence != "":
				report.occurrence = datetime.datetime.strptime(occurrence, "%d/%m/%Y").date()
				if report.occurrence.year <= 1900:
					raise Exception(self.lang['errors']['year_before_1900'])
			report.put()
			
			report._id = report.key().id()
			emailer.send_bug_report_to_admins(report, self.request.host+"/admin/bug-reports")
			report_id = report.key().id()
			
			values = {
				'success': True,
				'report_id': report_id,
			}
		except Exception as exc:
			stacktrace = traceback.format_exc()
			logging.error("%s", stacktrace)
			values = {
				'success': False,
				'error': exc.args[0]
			}
		self.response.out.write(json.dumps(values))

class RegistrationHandler(base_handlers.BaseApiHandler):
	def post(self):
		if self.beevote_user:
			values = {
				'success': False,
				'error': self.lang['errors']['already_registered']
			}
		else:
			user = users.get_current_user()
			user_id = user.user_id()
			name = self.request.get('name')
			surname = self.request.get('surname')
			email = user.email()
			language = 'en'
			if name == "":
				values = {
					'success': False,
					'error': self.lang['errors']['name_required']
				}
			elif surname == "":
				values = {
					'success': False,
					'error': self.lang['errors']['surname_required']
				}
			else:
				beevote_user = models.BeeVoteUser(
					user_id = user_id,
					email = email,
					name = name,
					surname = surname,
					language = language,
					last_access = datetime.datetime.now(),
				)
				
				beevote_user.last_access = datetime.datetime.now()
				
				beevote_user.put()
				
				emailer.send_registration_notification(beevote_user, language, self.request.host)
				
				values = {
					'success': True
				}
		
		self.response.out.write(json.dumps(values))

class LogoutHandler(webapp2.RequestHandler):
	def get(self):
		self.redirect(users.create_logout_url('/'))

# End of handlers