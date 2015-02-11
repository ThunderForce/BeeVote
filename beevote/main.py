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
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import users

from google.appengine.api import mail

import models
import api
import html_strips
import time

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

class MainHandler(BaseHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			beevote_user = models.get_beevote_user_from_google_id(user.user_id())
			if not beevote_user:
				self.redirect("/register")
				return
			else:
				self.redirect('/home')
		else:
			values = {
				'login_url': users.create_login_url('/'),
			}
			write_template(self.response, 'index.html', values)

class HomeHandler(BaseHandler):
	def get(self):
		
		user = users.get_current_user()
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		
		groups = db.GqlQuery("SELECT * FROM Group").fetch(1000)
		
		topics=[]
		
		groups = [g for g in groups if not (not beevote_user.key() in g.members) and (g.members != [])]
		
		for group in groups:
			
			'''
			if (not beevote_user.key() in group.members) and (group.members != []):
				groups.remove(group)
			else: 
				topics_group = db.GqlQuery('SELECT * FROM Topic WHERE group = :1', group).fetch(1000)
				topics.extend(topics_group)
			'''
			
			if len(group.name) > 20:
				group.name_short = group.name[:16]
			
			topics_group = db.GqlQuery('SELECT * FROM Topic WHERE group = :1', group).fetch(1000)
			topics.extend(topics_group)
		
		values = {
			'groups' : groups,
			'topics' : topics,
			'user' : beevote_user,
		}
		write_template(self.response, 'groups-layout.html',values)

class ProfileHandler(BaseHandler):
	def get(self, user_id):
		# Use user_id to get user and put it in values
		values = {}
		write_template(self.response, 'user-profile.html', values)

class GroupImageHandler(webapp2.RequestHandler):
	def get(self, group_id):
		group_key = db.Key.from_path('Group', long(group_id))
		group = db.get(group_key)
		if group == None:
			self.error(404)
			self.response.out.write("Group "+group_id+" does not exist")
		else:
			if group.img != None:
				self.response.headers['Content-Type'] = 'image/png'
				self.response.headers['Content-Disposition'] = 'inline; filename="group-'+group_id+'.png"'
				
				self.response.out.write(group.img)
			else:
				self.error(404)
				self.response.out.write("Group "+group_id+" does not have an image")

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
		redirect_url = '/'
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
				
				mail.send_mail_to_admins(
					sender="BeeVote Registration Notifier <notify-registration@beevote.appspotmail.com>",
					subject="BeeVote registration request received",
					body="""
Dear BeeVote admin,

Your application has received the following registration request:
- User ID: {request.user_id}
- User email: {request.email}
- Name: {request.name}
- Surname: {request.surname}

Follow this link to see all requests:
{link}

The BeeVote Team
        """.format(request=request, link=self.request.host+"/admin/pending-requests"))
				
				mail.send_mail(
					sender='BeeVote Registration Notifier <registration-pending@beevote.appspotmail.com>',
					to=request.email,
					subject="BeeVote registration request pending",
					body="""
Dear {request.name} {request.surname},

Your registration request has been sent: you will receive an email when an administrator accepts your request.

Details of registration request:
- User ID: {request.user_id}
- User email: {request.email}
- Name: {request.name}
- Surname: {request.surname}

The BeeVote Team
""".format(request=request, link=self.request.host))
				
				redirect_url = '/registration-pending'	
			else:
				beevote_user = models.BeeVoteUser(
					user_id = user.user_id(),
					email = user.email(),
					name = name,
					surname = surname,
				)
				beevote_user.put()
				redirect_url = '/'	
		time.sleep(1.00)
		self.redirect(redirect_url)

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

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': '20beeVote15',
}

server =  os.environ.get("SERVER_SOFTWARE")


if server is None:
	debug = False  # Unexpected, disable DEBUG.
else:
	software, version = server.split("/", 1)
	debug = software == "Development"

app = webapp2.WSGIApplication([
	('/', MainHandler),
	('/group/(.*)/topic/(.*)/image', TopicImageHandler),
	('/group/(.*)/image', GroupImageHandler),
	('/home', HomeHandler),
	('/profile/(.*)', ProfileHandler),
	('/api/group/(.*)/topic/(.*)/proposal/(.*)/remove', api.RemoveProposalHandler),
	('/api/group/(.*)/members/remove', api.RemoveGroupMemberHandler),
	('/api/group/(.*)/members/add', api.AddGroupMemberHandler),
	('/api/group/(.*)/topic/(.*)/remove', api.RemoveTopicHandler),
	('/api/create-group', api.CreateGroupHandler),
	('/api/create-topic', api.CreateTopicHandler),
	('/api/create-proposal', api.CreateProposalHandler),
	('/api/create-vote', api.CreateVoteHandler),
	('/api/remove-vote', api.RemoveVoteHandler),
	('/api/load-proposal', api.LoadProposalHandler),
	('/api/load-votes', api.LoadVotesHandler),
	('/api/load-group-members', api.LoadGroupMembersHandler),
	('/api/group/(.*)/topic/(.*)', api.LoadTopicHandler),
	('/api/groups', api.LoadGroupsHandler),
	('/api/group/(.*)', api.LoadGroupHandler),
	('/api/user/(.*)', api.LoadUserHandler),
	('/html/topics', html_strips.TopicsHandler),
	('/html/groups', html_strips.GroupsHandler),
	('/html/group/(.*)/topic/(.*)', html_strips.TopicHandler),
	('/html/group/(.*)/members', html_strips.GroupMembersHandler),
	('/html/group/(.*)', html_strips.GroupHandler),
	('/register', RegistrationHandler),
	('/request-registration',RequestRegistrationHandler),
	('/registration-pending',RegistrationPendingHandler),
	('/logout', LogoutHandler)
], debug=debug, config=config)

app.error_handlers[401] = handle_401
app.error_handlers[404] = handle_404