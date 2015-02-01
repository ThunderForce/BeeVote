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

import os
import webapp2
import datetime
import json
import time
from google.appengine.ext import db
from google.appengine.api import users

import collections

import models

# Start of functions

def get_json(json_obj):
	return json.dumps(json_obj, indent=4, separators=(',', ': '))

def get_group_from_id(group_id):
	group_key = db.Key.from_path('Group', long(group_id))
	group = db.get(group_key)
	return group

def get_topic_from_id(group_id, topic_id):
	topic_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id))
	topic = db.get(topic_key)
	return topic

def get_proposal_from_id(group_id, topic_id, proposal_id):
	proposal_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id), 'Proposal', long(proposal_id))
	proposal = db.get(proposal_key)
	return proposal

def get_beevote_user_from_id(beevote_user_id):
	beevote_user_key = db.Key.from_path('BeeVoteUser', long(beevote_user_id))
	beevote_user = db.get(beevote_user_key)
	return beevote_user

def get_groups_by_membership(beevote_user):
	groups = db.GqlQuery("SELECT * FROM Group").fetch(1000)
	groups = [g for g in groups if not (not beevote_user.key() in g.members) and (g.members != [])]
	return groups

def get_topics_from_group(group):
	return db.GqlQuery('SELECT * FROM Topic WHERE group = :1', group).fetch(1000)

def get_proposals_from_topic(topic):
	return db.GqlQuery('SELECT * FROM Proposal WHERE topic = :1', topic).fetch(1000)

def get_votes_from_proposal(proposal):
	return db.GqlQuery('SELECT * FROM Vote WHERE proposal = :1', proposal).fetch(1000)

def fetch_user(beevote_user, arguments):
	user = collections.OrderedDict([
		('user_data_data', collections.OrderedDict([
			('name', beevote_user.name),
			('surname', beevote_user.surname),
			('email', beevote_user.email),
			('creation', str(beevote_user.creation)),
		]))
	])
	if 'is_current_user' in arguments and arguments['is_current_user']:
		groups = get_groups_by_membership(beevote_user)
		user['groups'] = fetch_groups(groups, arguments)
	return user

def fetch_group(group, arguments):
	group_json = collections.OrderedDict([
		('group_data', collections.OrderedDict([
			('name', group.name),
			('description', group.description),
			('creation', str(group.creation)),
		]))
	])
	if 'fetch_topics' in arguments and arguments['fetch_topics']:
		group_json['topics'] = fetch_topics_from_group(group, arguments)
	return group_json
	
def fetch_topic(topic, arguments):
	topic_dict = collections.OrderedDict([
		('title', topic.title),
		('description', topic.description),
		('deadline', str(topic.deadline) if topic.deadline else None),
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
		('title', proposal.title),
		('description', proposal.description),
	])
	if 'fetch_votes' in arguments and arguments['fetch_votes']:
		votes = get_votes_from_proposal(proposal)
		proposal_dict['vote_number'] = len(votes)
		proposal_dict['votes'] = fetch_votes(votes, arguments)
	return proposal_dict

def fetch_groups(groups, arguments):
	groups_ret = []
	for datastore_group in groups:
		group = fetch_group(datastore_group, arguments)
		groups_ret.append(group)
	return groups_ret

def fetch_topics_from_group(group, arguments):
	datastore_topics = get_topics_from_group(group)
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
	datastore_proposals = get_proposals_from_topic(topic)
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
		datastore_groups = get_groups_by_membership(beevote_user)
		arguments = {
			'fetch_topics': self.request.get('fetch_topics', 'false') == 'true',
			'evaluate_deadlines': self.request.get('evaluate_deadlines', 'false') == 'true',
			'fetch_proposals': self.request.get('fetch_proposals', 'false') == 'true',
		}
		groups = fetch_groups(datastore_groups, arguments)
		
		self.response.out.write(get_json(groups))

class LoadGroupHandler(BaseApiHandler):
	def get(self, group_id):
		user = users.get_current_user()
		group = get_group_from_id(group_id)
		if (not group):
			self.abort(404, detail="This group does not exist.")
		'''
		if not is_user_in_group(models.get_beevote_user_from_google_id(user.user_id()), group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		'''
		arguments = {
			'fetch_topics': self.request.get('fetch_topics', 'false') == 'true',
			'evaluate_deadlines': self.request.get('evaluate_deadlines', 'false') == 'true',
			'fetch_proposals': self.request.get('fetch_proposals', 'false') == 'true',
		}
		
		group_json = fetch_group(group, arguments)
		
		self.response.out.write(get_json(group_json))

class LoadTopicHandler(BaseApiHandler):
	def get(self, group_id, topic_id):
		user = users.get_current_user()
		group = get_group_from_id(group_id)
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
		
		topic = get_topic_from_id(group_id, topic_id)
		topic_json = fetch_topic(topic, arguments)
		
		self.response.out.write(get_json(topic_json))

class LoadUserHandler(BaseApiHandler):
	def get(self, user_id):
		user = users.get_current_user()
		current_beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		
		target_beevote_user = get_beevote_user_from_id(user_id)
		
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
		user = users.get_current_user()
		user_id = user.user_id()
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

class LoadProposalHandler(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
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

class LoadGroupMembersHandler(webapp2.RequestHandler):
	def get(self):
		group_id = self.request.get('group_id')
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		values = {
			'success': True,
			'members': group.members,
		}
		self.response.out.write(json.dumps(values))

class LogoutHandler(webapp2.RequestHandler):
	def get(self):
		self.redirect(users.create_logout_url('/'))

# End of handlers