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

def get_template(template_name, template_values={}, navbar_values={}):
	directory = os.path.dirname(__file__)
	basic_head_path = os.path.join(directory, os.path.join('templates', 'basic-head.html'))
	navbar_path = os.path.join(directory, os.path.join('templates', 'navbar.html'))

	user = users.get_current_user()
	if user:
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
	else:
		beevote_user = None
	
	def_navbar_values = {
		'user': beevote_user,
		'breadcumb': None,
		'feedback_url': 'https://docs.google.com/forms/d/1qFNWDzBg_g1kCyNajcO32ji6vflfdsEc1MUdC4Dowvk/viewform',
	}
	def_navbar_values.update(navbar_values)
	
	'''
	breadcumb: {
		previous_elements: [
			{
				title: "",
				href: "",
			},{
				title: "",
				href: "",
			}
		],
		current_element: {
			title: ""
		}
	}
	'''

	values = {
		'basic_head': template.render(basic_head_path, {}),
		'navbar': template.render(navbar_path, def_navbar_values),
	}
	
	values.update(template_values)

	path = os.path.join(directory, os.path.join('templates', template_name))
	return template.render(path, values)

def write_template(response, template_name, template_values={}, navbar_values={}):
	response.headers["Pragma"]="no-cache"
	response.headers["Cache-Control"]="no-cache, no-store, must-revalidate, pre-check=0, post-check=0"
	response.headers["Expires"]="Thu, 01 Dec 1994 16:00:00"
	response.out.write(get_template(template_name, template_values, navbar_values))

def is_user_in_group(beevote_user, group):
	if group.members == [] or beevote_user.key() in group.members:
		return True
	else:
		return False

# List or URLs that you can access without being "registered" in the app
public_urls = ["/", "/logout", "/register", "/request-registration", "/registration-pending"]

class BaseHandler(webapp2.RequestHandler):
	def __init__(self, request, response):
		self.initialize(request, response)
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

class MainHandler(BaseHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			beevote_user = models.get_beevote_user_from_google_id(user.user_id())
			if not beevote_user:
				self.redirect("/register")
				return
			else:
				# Here we can show the page with groups and topic (basically the home).
				# Until we don't have a home, the handler redirects to /groups.
				# When the home is ready we will remove the redirect
				self.redirect('/groups')
		else:
			values = {
				'login_url': users.create_login_url('/'),
			}
			write_template(self.response, 'index.html', values)

class TopicSampleHandler(BaseHandler):
	def get(self, group_id, topic_id):
		user = users.get_current_user()
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		if not is_user_in_group(beevote_user, group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		topic_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id))
		topic = db.get(topic_key)
		
		proposals = db.GqlQuery('SELECT * FROM Proposal WHERE topic = :1', topic).fetch(1000)
		
		# Adding a variable on each proposal containing the NUMBER of votes of the proposal
		for proposal in proposals:
			votes = db.GqlQuery("SELECT * FROM Vote WHERE proposal = :1 AND creator = :2", proposal, beevote_user)
			own_vote = votes.get()
			if own_vote:
				proposal.already_voted = True
			else:
				proposal.already_voted = False
			proposal.vote_number = len(proposal.vote_set.fetch(1000))
		
		# Sorting the proposal according to vote number
		proposals = sorted(proposals, key=lambda proposal: proposal.vote_number, reverse=True)

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
			'proposals': proposals,
		}
		navbar_values = {
			'breadcumb': {
				'previous_elements': [
					{
						'title': group.name,
						'href': "/group/"+str(group.key().id()),
					}
				],
				'current_element': {
					'title': topic.title,
				}
			}
		}
		write_template(self.response, 'topic-layout.html', values, navbar_values=navbar_values)

class GroupsHandler(BaseHandler):
	def get(self):
		user = users.get_current_user()
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		groups = db.GqlQuery("SELECT * FROM Group").fetch(1000)
		for group in groups:
			if (not beevote_user.key() in group.members) and (group.members != []):
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
		if not is_user_in_group(models.get_beevote_user_from_google_id(user.user_id()), group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		topics = db.GqlQuery('SELECT * FROM Topic WHERE group = :1', group).fetch(20)
		currentdatetime = datetime.datetime.now()
		for topic in topics:
			if topic.deadline != None:
				topic.expired = topic.deadline < currentdatetime
		values = {
			'group': group,
			'topics': topics,
		}
		navbar_values = {
			'breadcumb': {
				'previous_elements': [],
				'current_element': {
					'title': group.name,
				}
			}
		}
		write_template(self.response, 'topics-layout.html', values, navbar_values=navbar_values)

class GroupMembersHandler(BaseHandler):
	def get(self, group_id):
		user = users.get_current_user()
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		if not is_user_in_group(models.get_beevote_user_from_google_id(user.user_id()), group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		group.members_data = db.get(group.members)
		values = {
			'group': group,
		}
		navbar_values = {
			'breadcumb': {
				'previous_elements': [
					{
						'title': group.name,
						'href': "/group/"+str(group.key().id()),
					}
				],
				'current_element': {
					'title': 'Members',
				}
			}
		}
		write_template(self.response, 'group-members-layout.html', values, navbar_values=navbar_values)

class AddGroupMemberHandler(BaseHandler):
	def post(self, group_id):
		user = users.get_current_user()
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		if not is_user_in_group(models.get_beevote_user_from_google_id(user.user_id()), group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		email = self.request.get("email")
		beevote_user = db.GqlQuery('SELECT * FROM BeeVoteUser WHERE email = :1', email).get()
		if beevote_user:
			group.members.append(beevote_user.key())
			group.put()
		self.redirect("/group/"+group_id+"/members")

class RemoveGroupMemberHandler(BaseHandler):
	def post(self, group_id):
		user = users.get_current_user()
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		if not is_user_in_group(models.get_beevote_user_from_google_id(user.user_id()), group):
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
		if not is_user_in_group(models.get_beevote_user_from_google_id(user.user_id()), group):
			self.abort(401, detail="You are not authorized to see this group.<br>Click <a href='javascript:history.back();'>here</a> to go back, or <a href='/logout'>here</a> to logout.")
		
		proposal_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id), 'Proposal', long(proposal_id))
		proposal = db.get(proposal_key)

		votes = db.GqlQuery("SELECT * FROM Vote WHERE proposal = :1", proposal)
		vote_number = votes.count()
		
		user = users.get_current_user()
		user_id = user.user_id()
		beevote_user = models.get_beevote_user_from_google_id(user_id)
		votes = db.GqlQuery("SELECT * FROM Vote WHERE proposal = :1 AND creator = :2", proposal, beevote_user)
		own_vote = votes.get()
		if own_vote:
			already_voted = True
		else:
			already_voted = False
		if proposal.parent().deadline != None:
			currentdatetime = datetime.datetime.now()
			proposal.parent().expired = proposal.parent().deadline < currentdatetime
		values = {
			'proposal': proposal,
			'vote_number': vote_number,
			'already_voted': already_voted,
		}
		navbar_values = {
			'breadcumb': {
				'previous_elements': [
					{
						'title': group.name,
						'href': "/group/"+str(group.key().id()),
					},{
						'title': proposal.parent().title,
						'href': "/group/"+str(group.key().id())+"/topic/"+str(proposal.parent().key().id()),
					}
				],
				'current_element': {
					'title': proposal.title,
				}
			}
		}
		write_template(self.response, 'proposal-layout.html', values, navbar_values=navbar_values)


class ProfileHandler(BaseHandler):
	def get(self, user_id):
		# Use user_id to get user and put it in values
		values = {}
		write_template(self.response, 'user-profile.html', values)

class TopicImageHandler(webapp2.RequestHandler):
	def get(self, group_id, topic_id):
		topic_key = db.Key.from_path('Group', long(group_id), 'Topic', long(topic_id))
		topic = db.get(topic_key)
		if topic == None:
			self.error(404)
			self.response.out.write("Topic "+topic_id+" does not exist")
		else:
			if topic.img != None:
				self.response.headers['Content-Type'] = 'image/png'
				self.response.headers['Content-Disposition'] = 'inline; filename="topic-'+topic_id+'.png"'
				
				self.response.out.write(topic.img)
			else:
				self.error(404)
				self.response.out.write("Topic "+topic_id+" does not have an image")

class CreateTopicHandler(BaseHandler):
	def post(self):
		user = users.get_current_user()
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		group_id = self.request.get('groupId')
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)

		title = self.request.get('inputTopicName')
		what = self.request.get('inputWhat')
		where= self.request.get('inputWhere')
		date = self.request.get('inputDate')
		time = self.request.get('inputTime')
		deadline = self.request.get('inputDeadline')
		description = self.request.get('inputDescription')
		img = self.request.get('inputImg')
		tzoffset = self.request.get('timezoneOffset')
		topic = models.Topic(
			title=title,
			group=group,
			parent=group,
			creator=beevote_user,
			  )
		topic.activity = what
		topic.place = where
		if date != "":
			topic.date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
		if time != "":
			topic.time = datetime.datetime.strptime(time, '%H:%M').time()
		if deadline !="":
			topic.deadline = datetime.datetime.strptime(deadline, "%Y/%m/%d %H:%M")
		topic.description = description
		if img != "":
			topic.img = db.Blob(img)
		topic.put()
		self.redirect('/group/'+group_id)

class CreateProposalHandler(BaseHandler):
	def post(self):
		user = users.get_current_user()
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
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
			parent=topic,
			creator=beevote_user,
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
		proposal.put()
		self.redirect('/group/'+group_id+'/topic/'+topic_id)

class CreateGroupHandler(BaseHandler):
	def post(self):
		user = users.get_current_user()
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		name = self.request.get('inputGroupName')
		description = self.request.get('inputDescription')
		group = models.Group(
				name = name,
				creator = beevote_user,
			)
		group.description = description
		group.members.append(beevote_user.key())
		group.put()
		group_id = group.key().id() 
		self.redirect('/group/'+str(group_id))

class RegistrationHandler(BaseHandler):
	def get(self):
		if models.get_beevote_user_from_google_id(users.get_current_user().user_id()):
			self.redirect("/")
			return
		if models.get_registration_request_from_google_id(users.get_current_user().user_id()):
			self.redirect("/registration-pending")
			return
		values = {
			'is_user_admin': users.is_current_user_admin()
		}
		write_template(self.response, 'registration-form.html', values)

class RequestRegistrationHandler(BaseHandler):
	def get(self):
		self.redirect("/register")
		return
	def post(self):
		user = users.get_current_user()
		if models.get_beevote_user_from_google_id(user.user_id()) == None:
			name = self.request.get('name')
			surname = self.request.get('surname')
			if not users.is_current_user_admin():
				request = models.RegistrationRequest(
					user_id = user.user_id(),
					email = user.email(),
					name = name,
					surname = surname,
				)
				request.put()
				self.redirect('/registration-pending')
				return
			else:
				beevote_user = models.BeeVoteUser(
					user_id = user.user_id(),
					email = user.email(),
					name = name,
					surname = surname,
				)
				beevote_user.put()
				self.redirect('/')
				return
		self.redirect('/')

class RegistrationPendingHandler(BaseHandler):
	def get(self):
		user_id = users.get_current_user().user_id()
		if models.get_beevote_user_from_google_id(user_id):
			self.redirect("/")
			return
		request = models.get_registration_request_from_google_id(user_id)
		if not request:
			self.redirect("/register")
			return
		values = {
			'request': request,
		}
		write_template(self.response, 'registration-pending.html', values)

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
	('/register', RegistrationHandler),
	('/request-registration',RequestRegistrationHandler),
	('/registration-pending',RegistrationPendingHandler),
	('/logout', LogoutHandler)
], debug=True)

app.error_handlers[401] = handle_401
app.error_handlers[404] = handle_404