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
from webapp2_extras import sessions
import datetime
from datetime import timedelta
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import users

import models
import time

import language

# Start of handlers

def write_template(response, template_name, template_values={}):
	directory = os.path.dirname(__file__)
	path = os.path.join(directory, os.path.join('templates', template_name))
	template_values.update({'lang': language.en})
	rendered_template = template.render(path, template_values)
	response.headers["Pragma"]="no-cache"
	response.headers["Cache-Control"]="no-cache, no-store, must-revalidate, pre-check=0, post-check=0"
	response.headers["Expires"]="Thu, 01 Dec 1994 16:00:00"
	response.out.write(rendered_template)

def is_user_in_group(beevote_user, group):
	if group.members == [] or beevote_user.key() in group.members:
		return True
	else:
		return False

class BaseHandler(webapp2.RequestHandler):
	def __init__(self, request, response):
		self.initialize(request, response)
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

	def dispatch(self):
		# Get a session store for this request.
		self.session_store = sessions.get_store(request=self.request)

		try:
			# Dispatch the request.
			webapp2.RequestHandler.dispatch(self)
		finally:
			# Save all sessions.
			self.session_store.save_sessions(self.response)

	#@webapp2.cached_property
	def session(self):
		# Returns a session using the default cookie key.
		return self.session_store.get_session()

class GroupsHandler(BaseHandler):
	def get(self):
		
		time.sleep(0.5)
		
		groups = self.beevote_user.get_groups_by_membership()
		
		for group in groups:
			
			if len(group.name) > 20:
				group.name_short = group.name[:16]
		
		values = {
			'groups' : groups,
		}
		write_template(self.response, 'html/groups.html',values)

class GroupHandler(BaseHandler):
	def get(self, group_id):
		group = models.Group.get_from_id(long(group_id))
		if (not group):
			self.abort(404, detail="This group does not exist.")
		if not is_user_in_group(self.beevote_user, group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		group.member_list = db.get(group.members)
		topics = group.get_topics()
		currentdatetime = datetime.datetime.now()
		for topic in topics:
			if topic.deadline != None:
				topic.expired = topic.deadline < currentdatetime
				time_before_deadline = topic.deadline - currentdatetime
				topic.seconds_before_deadline = time_before_deadline.total_seconds()
				topic.time_before_deadline = {
					'seconds': time_before_deadline.seconds % 60,
					'minutes': (time_before_deadline.seconds/60) % 60,
					'hours': time_before_deadline.seconds/3600,
					'days': time_before_deadline.days,
				}
			else:
				topic.seconds_before_deadline = timedelta.max.total_seconds()
			if topic.creator.key() == self.beevote_user.key():
				topic.is_own = True
			else:
				topic.is_own = False
		
		if self.beevote_user.key() in group.admins:
			group.is_own = True
		else:
			group.is_own = False

		topics = sorted(topics, key=lambda topic: topic.seconds_before_deadline)
		group.topics = topics
		
		values = {
			'group': group,
		}
		write_template(self.response, 'html/group-overview.html', values)

class TopicsHandler(BaseHandler):
	def get(self):
		time.sleep(0.5)
		
		topics = self.beevote_user.get_topics_by_group_membership()

		currentdatetime = datetime.datetime.now()
		for topic in topics:
			if(topic.date != None):
				topic.formatted_date = topic.date.strftime("%A   %d %B %Y")
			if topic.deadline != None:
				topic.expired = topic.deadline < currentdatetime
				time_before_deadline = topic.deadline - currentdatetime
				topic.seconds_before_deadline = time_before_deadline.total_seconds()
				topic.time_before_deadline = {
					'seconds': time_before_deadline.seconds % 60,
					'minutes': (time_before_deadline.seconds/60) % 60,
					'hours': time_before_deadline.seconds/3600,
					'days': time_before_deadline.days,
				}
			else:
				topic.seconds_before_deadline = timedelta.max.total_seconds()
			if topic.creator.key() == self.beevote_user.key():
				topic.is_own = True
			else:
				topic.is_own = False
		topics = sorted(topics, key=lambda topic: topic.seconds_before_deadline)
		values = {
			'topics' : topics,
		}
		write_template(self.response, 'html/topics.html',values)

class GroupMembersHandler(BaseHandler):
	def get(self, group_id):
		group = models.Group.get_from_id(long(group_id))
		if (not group):
			self.abort(404, detail="This group does not exist.")
		if not is_user_in_group(self.beevote_user, group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		group.member_list = db.get(group.members)
		
		if group.admins == [] or self.beevote_user.key() in group.admins:
			admin = True
		else:
			admin = False
		values = {
			'user': self.beevote_user,
			'group': group,
			'admin': admin,
		}
		write_template(self.response, 'html/group-members.html', values)

class TopicHandler(BaseHandler):
	def get(self, group_id, topic_id):
		group = models.Group.get_from_id(long(group_id))
		if not is_user_in_group(self.beevote_user, group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		topic = models.Topic.get_from_id(group_id, topic_id)
		if (not topic):
			self.abort(404, detail="This topic does not exist.")
		if(topic.date != None):
			topic.formatted_date = topic.date.strftime("%A   %d %B %Y")
		if topic.creator.key() == self.beevote_user.key():
			topic.is_own = True
		else:
			topic.is_own = False
		if self.beevote_user.key() not in topic.non_participant_users:
			topic.participation = True
		else:
			topic.participation = False
		
		proposals = topic.get_proposals()
		
		# Adding a variable on each proposal containing the NUMBER of votes of the proposal
		for proposal in proposals:
			votes = db.GqlQuery("SELECT * FROM Vote WHERE proposal = :1 AND creator = :2", proposal, self.beevote_user)
			own_vote = votes.get()
			if own_vote:
				proposal.already_voted = True
			else:
				proposal.already_voted = False
			proposal.vote_number = len(proposal.vote_set.fetch(1000))
			if(proposal.date != None):
				proposal.formatted_date = proposal.date.strftime("%A   %d %B %Y")

		
		# Sorting the proposal according to vote number
		topic.proposals = sorted(proposals, key=lambda proposal: proposal.vote_number, reverse=True)

		# Evaluation about topic deadline
		if topic.deadline != None:
			currentdatetime = datetime.datetime.now()
			topic.expired = topic.deadline < currentdatetime
			time_before_deadline = topic.deadline - currentdatetime
			topic.time_before_deadline = {
				'seconds': time_before_deadline.seconds % 60,
				'minutes': (time_before_deadline.seconds/60) % 60,
				'hours': time_before_deadline.seconds/3600,
				'days': time_before_deadline.days,
			}
			
		values = {
			'topic': topic,
		}
		write_template(self.response, 'html/topic-overview.html', values)