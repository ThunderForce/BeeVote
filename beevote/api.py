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

import models

# Start of handlers

class CreateVoteHandler(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		group_id = self.request.get('group_id')
		topic_id = self.request.get('topic_id')
		proposal_id = self.request.get('proposal_id')
		proposal_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id), 'Proposal', long(proposal_id))
		proposal = db.get(proposal_key)
		if proposal.parent().deadline != None:
			currentdatetime = datetime.datetime.now()
			proposal.parent().expired = proposal.parent().deadline < currentdatetime
			if proposal.parent().expired:
				success = False
		else:
			user_id = user.user_id()
			email = user.email()
			vote = models.Vote(proposal=proposal, parent=proposal)
			vote.creator = user_id
			vote.email = email
			vote.put()
			time.sleep(0.25)
			success = True
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
		group_id = self.request.get('group_id')
		topic_id = self.request.get('topic_id')
		proposal_id = self.request.get('proposal_id')
		proposal_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id), 'Proposal', long(proposal_id))
		proposal = db.get(proposal_key)
		if proposal.parent().deadline != None:
			currentdatetime = datetime.datetime.now()
			proposal.parent().expired = proposal.parent().deadline < currentdatetime
			if proposal.parent().expired:
				success = False
		else:
			votes = db.GqlQuery("SELECT * FROM Vote WHERE proposal = :1 AND creator = :2", proposal, user_id)
			vote = votes.get()
			vote.delete()
			time.sleep(0.25)
			success = True;
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
				'email': vote.email,
			})
		values = {
			'success': True,
			'votes': votes,
		}
		self.response.out.write(json.dumps(values))

class LoadProposalHandler(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		user_id = user.user_id()
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
				'creator_email': proposal.email,
				'activity': proposal.activity,
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