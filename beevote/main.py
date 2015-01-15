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
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import users

import models
import api

# Start of handlers

# List or URLs that you can access without being "registered" in the app
public_urls = ["/", "/logout"]

def get_template(template_name, template_values={}):
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

def write_template(response, template_name, template_values={}):
	response.headers["Pragma"]="no-cache"
	response.headers["Cache-Control"]="no-cache, no-store, must-revalidate, pre-check=0, post-check=0"
	response.headers["Expires"]="Thu, 01 Dec 1994 16:00:00"
	response.out.write(get_template(template_name, template_values))

def is_user_in_group(user, group):
	if user.email() in group.members:
		return True
	else:
		return False

class BaseHandler(webapp2.RequestHandler):
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
					self.abort(401, detail="You are not authorized to use this app. Ask the administrator to allow your Google Account to access this app by giving him your email: <b>"+users.get_current_user().email()+"</b><br>Click <a href='/logout'>here</a> to logout.")

class MainHandler(BaseHandler):
	def get(self):
		write_template(self.response, 'index.html')

class TopicSampleHandler(BaseHandler):
	def get(self, group_id, topic_id):
		user = users.get_current_user()
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		if not is_user_in_group(user, group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
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
		write_template(self.response, 'topic-layout.html', values)

class GroupsHandler(BaseHandler):
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
		write_template(self.response, 'groups-layout.html',values)

class GroupHandler(BaseHandler):
	def get(self, group_id):
		user = users.get_current_user()
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		if not is_user_in_group(user, group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		topics = db.GqlQuery('SELECT * FROM Topic WHERE group = :1', group).fetch(20)
		values = {
			'group': group,
			'topics': topics,
		}
		write_template(self.response, 'topics-layout.html', values)

class GroupMembersHandler(BaseHandler):
	def get(self, group_id):
		user = users.get_current_user()
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		if not is_user_in_group(user, group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		values = {
			'group': group,
		}
		write_template(self.response, 'group-members-layout.html', values)

class AddGroupMemberHandler(BaseHandler):
	def post(self, group_id):
		user = users.get_current_user()
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		if not is_user_in_group(user, group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		email = self.request.get("email")
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		group.members.append(email)
		group.put()
		self.redirect("/group/"+group_id+"/members")

class RemoveGroupMemberHandler(BaseHandler):
	def post(self, group_id):
		user = users.get_current_user()
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		if not is_user_in_group(user, group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		email = self.request.get("email")
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		group.members.remove(email)
		group.put()
		self.redirect("/group/"+group_id+"/members")

class ProposalHandler(BaseHandler):
	def get(self, group_id, topic_id, proposal_id):
		user = users.get_current_user()
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		if not is_user_in_group(user, group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		
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
		write_template(self.response, 'proposal-layout.html', values)


class ProfileHandler(BaseHandler):
	def get(self, user_id):
		# Use user_id to get user and put it in values
		values = {}
		write_template(self.response, 'user-profile.html', values)

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

class CreateTopicHandler(BaseHandler):
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

class CreateProposalHandler(BaseHandler):
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

class CreateGroupHandler(BaseHandler):
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
		
# End of handlers

def handle_401(request, response, exception):
	response.set_status(401)
	write_template(response, 'errors/401.html', {'detail': exception.detail})

def handle_404(request, response, exception):
	response.set_status(404)
	write_template(response, 'not_found.html', {'url': request.path})

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
	('/logout', LogoutHandler)
], debug=True)

app.error_handlers[401] = handle_401
app.error_handlers[404] = handle_404