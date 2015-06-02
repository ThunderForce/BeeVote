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

from datetime import timedelta
import datetime
import time

from google.appengine.ext import ndb

import base_handlers
import constants
import models


# Start of handlers
class GroupsHandler(base_handlers.BaseHtmlStripsHandler):
	def get(self):
		
		time.sleep(0.5)
		
		groups = self.beevote_user.get_groups_by_membership()
		
		for group in groups:
			
			if len(group.name) > 20:
				group.name_short = group.name[:16]
		
		values = {
			'groups' : groups,
		}
		base_handlers.write_template(self.response, 'html/groups.html',values)

class GroupHandler(base_handlers.BaseHtmlStripsHandler):
	def get(self, group_id):
		group = models.Group.get_from_id(long(group_id))
		if (not group):
			self.abort(404, detail="This group does not exist.")
		if not group.contains_user(self.beevote_user):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		group.member_list = ndb.get_multi(group.members)
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
			if topic.creator == self.beevote_user.key:
				topic.is_own = True
			else:
				topic.is_own = False
		
		if self.beevote_user.key in group.admins:
			group.is_own = True
		else:
			group.is_own = False

		topics = sorted(topics, key=lambda topic: topic.seconds_before_deadline)
		group.topics = topics
		
		personal_settings = models.GroupPersonalSettings.get_settings(self.beevote_user, group)
		
		values = {
			'group': group,
			'personal_settings': personal_settings,
		}
		models.GroupAccess.update_specific_access(group, self.beevote_user)
		base_handlers.write_template(self.response, 'html/group-overview.html', values)

class TopicsHandler(base_handlers.BaseHtmlStripsHandler):
	def get(self):
		time.sleep(0.5)
		
		topics = self.beevote_user.get_topics_by_group_membership()

		currentdatetime = datetime.datetime.now()
		for topic in topics:
			if(topic.date != None):
				topic.formatted_date = topic.date.strftime(constants.topic_date_format)
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
			if topic.creator == self.beevote_user.key:
				topic.is_own = True
			else:
				topic.is_own = False
		topics = sorted(topics, key=lambda topic: topic.seconds_before_deadline)
		values = {
			'topics' : topics,
		}
		base_handlers.write_template(self.response, 'html/topics.html',values)

class GroupMembersHandler(base_handlers.BaseHtmlStripsHandler):
	def get(self, group_id):
		group = models.Group.get_from_id(long(group_id))
		if (not group):
			self.abort(404, detail="This group does not exist.")
		if not group.contains_user(self.beevote_user):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		group.member_list = ndb.get_multi(group.members)
		
		if group.admins == [] or self.beevote_user.key in group.admins:
			admin = True
		else:
			admin = False
		values = {
			'user': self.beevote_user,
			'group': group,
			'admin': admin,
		}
		base_handlers.write_template(self.response, 'html/group-members.html', values)

class TopicHandler(base_handlers.BaseHtmlStripsHandler):
	def get(self, group_id, topic_id):
		group = models.Group.get_from_id(long(group_id))
		if not group.contains_user(self.beevote_user):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		topic = models.Topic.get_from_id(long(group_id), long(topic_id))
		if (not topic):
			self.abort(404, detail="This topic does not exist.")
		if(topic.date != None):
			topic.formatted_date = topic.date.strftime(constants.topic_date_format)
		if topic.creator == self.beevote_user.key:
			topic.is_own = True
		else:
			topic.is_own = False
		if self.beevote_user.key not in topic.non_participant_users:
			topic.participation = True
		else:
			topic.participation = False
		
		proposals = topic.get_proposals()
		
		# Adding a variable on each proposal containing the NUMBER of votes of the proposal
		for proposal in proposals:
			votes = ndb.gql("SELECT * FROM Vote WHERE proposal = :1 AND creator = :2", proposal.key, self.beevote_user.key)
			own_vote = votes.get()
			if own_vote:
				proposal.already_voted = True
			else:
				proposal.already_voted = False
			proposal.vote_number = len(proposal.get_votes())
			proposal.comment_number = len(proposal.get_comments())
			if(proposal.date != None):
				proposal.formatted_date = proposal.date.strftime(constants.proposal_date_format)
		
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
		
		personal_settings = models.TopicPersonalSettings.get_settings(self.beevote_user, topic)
		values = {
			'topic': topic,
			'personal_settings': personal_settings
		}
		models.TopicAccess.update_specific_access(topic, self.beevote_user)
		base_handlers.write_template(self.response, 'html/topic-overview.html', values)