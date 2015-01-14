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

# List or URLs that you can access without being "registered" in the app
public_urls = ["/", "/logout"]

class BaseHandler(webapp2.RequestHandler):
	def get_template(self, template_name, template_values={}):
		directory = os.path.dirname(__file__)
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
		return template.render(path, values)
	def __init__(self, request, response):
		self.initialize(request, response)
		if not self.request.path in public_urls:
			allowed = users.is_current_user_admin()
			if not allowed:
				current_user_email = users.get_current_user().email()
				allowed_users = db.GqlQuery("SELECT * FROM BeeVoteUser").run()
				for allowed_user in allowed_users:
					if allowed_user.email == current_user_email:
						allowed = True
						break
				if not allowed:
					template = self.get_template("errors/401.html", template_values={'detail': "You are not authorized to use this app. Ask the administrator to allow your Google Account to access this app by giving him your email: <b>"+users.get_current_user().email()+"</b><br>Click <a href='/logout'>here</a> to logout."})
					self.abort(401, body_template=template)

class BasicPageHandler(BaseHandler):
	def write_template(self, template_name, template_values={}):
		
		self.response.headers["Pragma"]="no-cache"
		self.response.headers["Cache-Control"]="no-cache, no-store, must-revalidate, pre-check=0, post-check=0"
		self.response.headers["Expires"]="Thu, 01 Dec 1994 16:00:00"
		
		self.response.out.write(self.get_template(template_name, template_values))

class MainHandler(BasicPageHandler):
	def get(self):
		self.write_template('index.html')

class TopicSampleHandler(BasicPageHandler):
	def get(self, group_id, topic_id):
		topic_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id))
		topic = db.get(topic_key)
		
		proposals = db.GqlQuery('SELECT * FROM Proposal WHERE topic = :1', topic).fetch(10)
		
		# Adding a variable on each proposal containing the NUMBER of votes of the proposal
		for proposal in proposals:
			proposal.vote_number = len(proposal.vote_set.fetch(1000))
		
		# Sorting the proposal according to vote number
		proposals = sorted(proposals, key=lambda proposal: proposal.vote_number, reverse=True)
		
		values = {
			'topic': topic,
			'proposals': proposals,
		}
		self.write_template('topic-layout.html', values)

class GroupsHandler(BasicPageHandler):
	def get(self):
		user = users.get_current_user()
		email = user.email()
		groups = db.GqlQuery("SELECT * FROM Group").fetch(100)
		for group in groups:
			if (not email in group.members) and (group.members != []):
				groups.remove(group)
		values = {
			'groups' : groups
		}
		self.write_template('groups-layout.html',values)

class GroupHandler(BasicPageHandler):
	def get(self, group_id):
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		topics = db.GqlQuery('SELECT * FROM Topic WHERE group = :1', group).fetch(20)
		values = {
			'group': group,
			'topics': topics,
		}
		self.write_template('topics-layout.html', values)

class GroupMembersHandler(BasicPageHandler):
	def get(self, group_id):
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		values = {
			'group': group,
		}
		self.write_template('group-members-layout.html', values)

class AddGroupMemberHandler(BasicPageHandler):
	def post(self, group_id):
		email = self.request.get("email")
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		group.members.append(email)
		group.put()
		self.redirect("/group/"+group_id+"/members")

class RemoveGroupMemberHandler(BasicPageHandler):
	def post(self, group_id):
		email = self.request.get("email")
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		group.members.remove(email)
		group.put()
		self.redirect("/group/"+group_id+"/members")

class ProposalHandler(BasicPageHandler):
	def get(self, group_id, topic_id, proposal_id):
		proposal_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id), 'Proposal', long(proposal_id))
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


class ProfileHandler(BasicPageHandler):
	def get(self, user_id):
		# Use user_id to get user and put it in values
		values = {}
		self.write_template('user-profile.html', values)

class TopicImageHandler(webapp2.RequestHandler):
	def get(self, group_id, topic_id):
		topic_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id))
		topic = db.get(topic_key)
		# Need to set header ContentType as image
		if topic == None:
			self.error(404)
			self.response.out.write("Topic "+topic_id+" does not exist")
		else:
			if topic.img != None:
				self.response.out.write(topic.img)
			else:
				self.error(404)
				self.response.out.write("Topic "+topic_id+" does not have an image")

class CreateTopicHandler(BasicPageHandler):
	def post(self):
		user = users.get_current_user()
		user_id = user.user_id()
		email = user.email()
		group_id = self.request.get('groupId')
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)


		title = self.request.get('inputTopicName')
		what = self.request.get('inputWhat')
		where= self.request.get('inputWhere')
		date = self.request.get('inputDate')
		time = self.request.get('inputTime')
		description = self.request.get('inputDescription')
		img = self.request.get('inputImg')
		topic = models.Topic(
			title=title,
			group=group,
			parent=group
			  )
		topic.activity = what
		topic.place = where
		if date != "":
			topic.date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
		if time != "":
			topic.time = datetime.datetime.strptime(time, '%H:%M').time()
		topic.description = description
		topic.creator = user_id
		topic.email=email
		if img != "":
			topic.img = db.Blob(img)
		topic.put()
		self.redirect('/group/'+group_id)

class CreateProposalHandler(BasicPageHandler):
	def post(self):
		user = users.get_current_user()
		user_id = user.user_id()
		email = user.email()
		title = self.request.get('inputProposalName')
		what = self.request.get('inputWhat')
		where = self.request.get('inputWhere')
		date = self.request.get('inputDate')
		time = self.request.get('inputTime')
		description = self.request.get('inputDescription')
		topic_id = self.request.get('topicId')
		group_id = self.request.get('groupId')
		topic_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id))
		topic = db.get(topic_key)
		proposal = models.Proposal(
			title=title,
			topic=topic,
			parent=topic
		)
		if what != "":
			proposal.activity = what
		if where != "":
			proposal.place = where
		if date != "":
			proposal.date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
		if time != "":
			proposal.time = datetime.datetime.strptime(time, '%H:%M').time()
		proposal.description = description
		proposal.creator = user_id
		proposal.email=email
		proposal.put()
		self.redirect('/group/'+group_id+'/topic/'+topic_id)

class CreateGroupHandler(BasicPageHandler):
	def post(self):
		user = users.get_current_user()
		email = user.email()
		name = self.request.get('inputGroupName')
		description = self.request.get('inputDescription')
		group = models.Group(
				name = name,
			)
		group.description = description
		group.members.append(email)
		group.put()
		group_id = group.key().id() 
		self.redirect('/group/'+str(group_id))

class LogoutHandler(webapp2.RequestHandler):
	def get(self):
		self.redirect(users.create_logout_url('/'))

class NotFoundPageHandler(BasicPageHandler):
	def get(self):
		self.error(404)
		self.write_template('not_found.html', {'url': self.request.path})
		
# End of handlers

def handle_401(request, response, exception):
	response.set_status(401)
	response.write(exception.body_template)

app = webapp2.WSGIApplication([
	('/', MainHandler),
	('/group/(.*)/members/remove', RemoveGroupMemberHandler),
	('/group/(.*)/members/add', AddGroupMemberHandler),
	('/group/(.*)/members', GroupMembersHandler),
	('/group/(.*)/topic/(.*)/image', TopicImageHandler),
	('/group/(.*)/topic/(.*)/proposal/(.*)', ProposalHandler),
	('/group/(.*)/topic/(.*)', TopicSampleHandler), #topic-layout
	('/groups', GroupsHandler),
	('/group/(.*)', GroupHandler),			#topics-layout.html
	('/profile/(.*)', ProfileHandler),
	('/create-topic', CreateTopicHandler),
	('/create-proposal', CreateProposalHandler),
	('/create-group',CreateGroupHandler),
	('/api/create-vote', api.CreateVoteHandler),
	('/api/remove-vote', api.RemoveVoteHandler),
	('/api/load-proposal', api.LoadProposalHandler),
	('/api/load-votes', api.LoadVotesHandler),
	('/api/load-group-members', api.LoadGroupMembersHandler),
	('/logout', LogoutHandler),
	('/.*', NotFoundPageHandler)
], debug=True)

app.error_handlers[401] = handle_401