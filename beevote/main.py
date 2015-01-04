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
#import json
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import users

import models
import api

# Start of handlers

class BasicPageHandler(webapp2.RequestHandler):
	def write_template(self, template_name, template_values={}):
	
		directory = os.path.dirname(__file__)
		#import_path = os.path.join(directory, os.path.join('templates', 'basic-head.html'))
		basic_head_path = os.path.join(directory, os.path.join('templates', 'basic-head.html'))
		navbar_path = os.path.join(directory, os.path.join('templates', 'navbar.html'))

		user = users.get_current_user()

		val_user = {
			'user': user,
		}

		values = {
			'basic_head': template.render(basic_head_path, {}),
			'navbar': template.render(navbar_path, val_user),
		}
		
		values.update(template_values)

		path = os.path.join(directory, os.path.join('templates', template_name))
		self.response.out.write(template.render(path, values))

class MainHandler(BasicPageHandler):
	def get(self):
		self.write_template('index.html')

class TopicSampleHandler(BasicPageHandler):
	def get(self):
		topic_key = db.Key.from_path('Topic', long(self.request.get('id')))
		topic = db.get(topic_key)
		
		proposals = db.GqlQuery('SELECT * FROM Proposal WHERE topic = :1', topic).fetch(10)
		values = {
			'topic': topic,
			'proposals': proposals,
		}
		self.write_template('topic-layout.html', values)

class GroupListHandler(BasicPageHandler):
	def get(self):
		self.write_template('groups-list-layout.html')

class GroupHandler(BasicPageHandler):
	def get(self):
		topics = db.GqlQuery('SELECT * FROM Topic').fetch(10)
		values = {'topics': topics}
		self.write_template('topics-layout.html', values)

class ProposalHandler(BasicPageHandler):
	def get(self):
		proposal_key = db.Key.from_path('Proposal', long(self.request.get('id')))
		proposal = db.get(proposal_key)
		votes = db.GqlQuery("SELECT * FROM Vote WHERE proposal = :1", proposal)
		vote_number = votes.count()
		
		user = users.get_current_user()
		user_id = user.user_id()
		votes = db.GqlQuery("SELECT * FROM Vote WHERE proposal = :1 AND creator = :2", proposal, user_id)
		own_vote = votes.get()
		if own_vote:
			already_voted = True
		else:
			already_voted = False
		values = {
			'proposal': proposal,
			'vote_number': vote_number,
			'already_voted': already_voted,
		}
		self.write_template('proposal-layout.html', values)

#class NewTopicHandler(BasicPageHandler):
#	def get(self):
#		self.write_template('topic-form.html')
#		
#class NewProposalHandler(BasicPageHandler):
#	def get(self):
#		topic_id = self.request.get('topic')
#		self.write_template('proposal-form.html', {'topic_id': topic_id})

class ProfileHandler(BasicPageHandler):
	def get(self, user_id):
		# Use user_id to get user and put it in values
		values = {}
		self.write_template('profile-layout.html', values)

class CreateTopicHandler(BasicPageHandler):
	def post(self):
		user = users.get_current_user()
		user_id = user.user_id()
		title = self.request.get('inputTopicName')
		what = self.request.get('inputWhat')
		where= self.request.get('inputWhere')
		date = self.request.get('inputDate')
		time = self.request.get('inputTime')
		description = self.request.get('inputDescription')
		img = self.request.get('inputImg')
		topic = models.Topic(title=title)
		topic.activity = what
		topic.place = where
		if date != "":
			topic.date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
		if time != "":
			topic.time = datetime.datetime.strptime(time, '%H:%M').time()
		topic.description = description
		topic.creator = user_id
		topic.img = db.Blob(img)
		topic.put()
		self.redirect('/group')

class CreateProposalHandler(BasicPageHandler):
	def post(self):
		user = users.get_current_user()
		user_id = user.user_id()
		title = self.request.get('inputProposalName')
		what = self.request.get('inputWhat')
		where= self.request.get('inputWhere')
		date = self.request.get('inputDate')
		time = self.request.get('inputTime')
		description = self.request.get('inputDescription')
		topic_id = self.request.get('topicId')
		topic_key = db.Key.from_path('Topic', long(topic_id))
		topic = db.get(topic_key)
		proposal = models.Proposal(
			title=title,
			topic=topic,
		)
		proposal.activity = what
		proposal.place = where
		if date != "":
			proposal.date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
		if time != "":
			proposal.time = datetime.datetime.strptime(time, '%H:%M').time()
		proposal.description = description
		proposal.creator = user_id
		proposal.put()
		self.redirect('/view-topic?id='+topic_id)

'''
class CreateVoteHandler(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		user_id = user.user_id()
		proposal_id = self.request.get('proposal_id')
		proposal_key = db.Key.from_path('Proposal', long(proposal_id))
		proposal = db.get(proposal_key)
		vote = models.Vote(proposal=proposal)
		vote.creator = user_id
		vote.put()
		votes = db.GqlQuery("SELECT * FROM Vote WHERE proposal = :1", proposal)
		vote_number = votes.count()
		values = {
			'success': True,
			'vote_number': vote_number,
		}
		self.response.out.write(json.dumps(values))

class RemoveVoteHandler(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		user_id = user.user_id()
		proposal_id = self.request.get('proposal_id')
		proposal_key = db.Key.from_path('Proposal', long(proposal_id))
		proposal = db.get(proposal_key)
		votes = db.GqlQuery("SELECT * FROM Vote WHERE proposal = :1 AND creator = :2", proposal, user_id)
		vote = votes.get()
		vote.delete()
		votes = db.GqlQuery("SELECT * FROM Vote WHERE proposal = :1", proposal)
		vote_number = votes.count()
		values = {
			'success': True,
			'vote_number': vote_number,
		}
		self.response.out.write(json.dumps(values))

class LoadVotesHandler(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()
		user_id = user.user_id()
		proposal_id = self.request.get('proposal_id')
		proposal_key = db.Key.from_path('Proposal', long(proposal_id))
		proposal = db.get(proposal_key)
		votes_db = db.GqlQuery("SELECT * FROM Vote WHERE proposal = :1", proposal).fetch(10)
		votes = []
		for vote in votes_db:
			votes.append({
				'creator': vote.creator,
			})
		values = {
			'success': True,
			'votes': votes,
		}
		self.response.out.write(json.dumps(values))
'''

class LogoutHandler(webapp2.RequestHandler):
	def get(self):
		self.redirect(users.create_logout_url('/'))

class NotFoundPageHandler(BasicPageHandler):
	def get(self):
		self.error(404)
		self.write_template('not_found.html', {'url': self.request.path})

# End of handlers

app = webapp2.WSGIApplication([
	('/', MainHandler),
	('/view-topic', TopicSampleHandler), #topic-layout
	('/groups', GroupListHandler),
	('/group', GroupHandler),			#topics-layout.html
	('/view-proposal', ProposalHandler),
	#('/new-topic', NewTopicHandler),
	#('/new-proposal', NewProposalHandler),
	('/profile/(.*)', ProfileHandler),
	('/create-topic', CreateTopicHandler),
	('/create-proposal', CreateProposalHandler),
	('/api/create-vote', api.CreateVoteHandler),
	('/api/remove-vote', api.RemoveVoteHandler),
	('/api/load-votes', api.LoadVotesHandler),
	('/logout', LogoutHandler),
	('/.*', NotFoundPageHandler)
], debug=True)
