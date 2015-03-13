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

import datetime
import os
import time

from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.api.images import Image
from google.appengine.ext import db
from google.appengine.ext.webapp import template
import webapp2
from webapp2_extras import sessions

import api
import html_strips
import language
import models


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


	if not beevote_user or not beevote_user.language:
		lang_package= 'en'
	else:
		lang_package=beevote_user.language
	
	def_navbar_values = {
		'user': beevote_user,
		'breadcumb': None,
		'feedback_url': 'https://docs.google.com/forms/d/1qFNWDzBg_g1kCyNajcO32ji6vflfdsEc1MUdC4Dowvk/viewform',
		'lang': language.lang[lang_package],
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
		'lang': language.lang[lang_package],
	}
	
	values.update(template_values)

	path = os.path.join(directory, os.path.join('templates', template_name))
	return template.render(path, values)

def write_template(response, template_name, template_values={}, navbar_values={}):
	response.headers["Pragma"]="no-cache"
	response.headers["Cache-Control"]="no-cache, no-store, must-revalidate, max-age=0, pre-check=0, post-check=0"
	response.headers["Expires"]="Thu, 01 Dec 1994 16:00:00"
	response.out.write(get_template(template_name, template_values, navbar_values))

def is_user_in_group(beevote_user, group):
	if group.members == [] or beevote_user.key() in group.members:
		return True
	else:
		return False

def resize_image(image_data, width, height):
	image = Image(image_data=image_data)
	if (image.width / float(width)) > (image.height / float(height)):
		image.resize(height=height)
		image = Image(image_data=image.execute_transforms())
		x_crop_ratio = (image.width - width) / float(image.width * 2)
		image.crop(x_crop_ratio, 0.0, 1-x_crop_ratio, 1.0)
	else:
		image.resize(width=width)
		image = Image(image_data=image.execute_transforms())
		y_crop_ratio = (image.height - height) / float(image.height * 2)
		image.crop(0.0, y_crop_ratio, 1.0, 1-y_crop_ratio)
	return image.execute_transforms()

# List or URLs that you can access without being "registered" in the app
public_urls = ["/", "/logout"]
google_user_urls = ["/", "/logout", "/register"]

class BaseHandler(webapp2.RequestHandler):
	def __init__(self, request, response):
		self.initialize(request, response)
		self.beevote_user = None
		if not self.request.path in public_urls:
			user = users.get_current_user()
			if not user:
				url = request.url
				if request.query_string != "":
					url += '?' + request.query_string
				self.abort(401, headers={'Location': users.create_login_url(url)})
				#self.redirect(users.create_login_url(url))
				#return
			if not self.request.path in google_user_urls:
				
				self.beevote_user = models.get_beevote_user_from_google_id(user.user_id())
				
				if not self.beevote_user:
					self.abort(401, headers={'Location': '/register'})
					#self.abort(401, detail="You are not yet registered in the application")
					#self.redirect("/register")
					return

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
			if not self.beevote_user and not models.get_beevote_user_from_google_id(user.user_id()):
				self.redirect("/register")
				return
			else:
				self.redirect('/home')
		else:
			values = {
				'login_url': users.create_login_url('/home'),
			}
			write_template(self.response, 'index.html', values)

class HomeHandler(BaseHandler):
	def get(self, group_id, topic_id):
		
		if not self.beevote_user:
			self.redirect("/register")
			return
		
		last_access = self.beevote_user.last_access if hasattr(self.beevote_user, 'last_access') else datetime.datetime.min
		self.beevote_user.last_access = datetime.datetime.now()
		self.beevote_user.put()
		
		feature_changes = db.GqlQuery("SELECT * FROM FeatureChange WHERE creation > :1", last_access).fetch(1000)
		
		values = {
			'user' : self.beevote_user,
			'feature_changes': feature_changes,
			'group_id': group_id,
			'topic_id': topic_id,
		}
		write_template(self.response, 'groups-layout.html',values)
class EditUserHandler(BaseHandler):
	def get(self):
		# Use user_id to get user and put it in values
		values = {
			'user' : self.beevote_user,
		}
		write_template(self.response, 'edit-user.html', values)
		
class ProfileHandler(BaseHandler):
	def get(self, user_id):
		# Use user_id to get user and put it in values
		values = {}
		write_template(self.response, 'user-profile.html', values)

class UserImageHandler(webapp2.RequestHandler):
	def get(self, user_id):
		user_key = db.Key.from_path('BeeVoteUser', long(user_id))
		user = db.get(user_key)
		if user == None:
			self.error(404)
			self.response.out.write("User "+user_id+" does not exist")
		else:
			if user.img != None:
				self.response.headers['Content-Type'] = 'image/png'
				self.response.headers['Content-Disposition'] = 'inline; filename="user-'+user_id+'.png"'
				try:
					width = int(self.request.get('width'))
					height = int(self.request.get('height'))
					self.response.out.write(resize_image(user.img, width, height))
				except:
					self.response.out.write(user.img)
			else:
				self.error(404)
				self.response.out.write("User "+user_id+" does not have an image")

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
				try:
					width = int(self.request.get('width'))
					height = int(self.request.get('height'))
					self.response.out.write(resize_image(group.img, width, height))
				except:
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
				try:
					width = int(self.request.get('width'))
					height = int(self.request.get('height'))
					self.response.out.write(resize_image(topic.img, width, height))
				except:
					self.response.out.write(topic.img)
			else:
				self.error(404)
				self.response.out.write("Topic "+topic_id+" does not have an image")

class RegistrationHandler(BaseHandler):
	def get(self):
		user_id = users.get_current_user().user_id()
		if self.beevote_user or models.get_beevote_user_from_google_id(user_id):
			self.redirect("/")
			return
		values = {
			'is_user_admin': users.is_current_user_admin()
		}
		write_template(self.response, 'registration-form.html', values)

class ReportBugHandler(BaseHandler):
	def get(self):
		values = {}
		write_template(self.response, 'report-bug.html', values)

class LogoutHandler(webapp2.RequestHandler):
	def get(self):
		self.redirect(users.create_logout_url('/'))
		
# End of handlers

def handle_401(request, response, exception):
	if 'Location' in exception.headers and exception.headers['Location']:
		response.set_status(302)
		response.headers['Location'] = exception.headers['Location']
		return
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
	('/user/(.*)/image', UserImageHandler),
	('/group/(.*)/topic/(.*)/image', TopicImageHandler),
	('/group/(.*)/image', GroupImageHandler),
	webapp2.Route('/group/<group_id>/topic/<topic_id>', handler=HomeHandler),
	webapp2.Route('/group/<group_id>', handler=HomeHandler, defaults={'topic_id': None}),
	webapp2.Route('/home', handler=HomeHandler, defaults={'group_id': None, 'topic_id': None}),
	#('/home', HomeHandler),
	('/profile/(.*)', ProfileHandler),
	('/report-bug', ReportBugHandler),
	('/api/group/(.*)/topic/(.*)/proposal/(.*)/remove', api.RemoveProposalHandler),
	('/api/group/(.*)/members/remove', api.RemoveGroupMemberHandler),
	('/api/group/(.*)/members/add', api.AddGroupMemberHandler),
	('/api/group/(.*)/topic/(.*)/remove-participation', api.RemoveParticipationHandler),
	('/api/group/(.*)/topic/(.*)/add-participation', api.AddParticipationHandler),
	('/api/group/(.*)/topic/(.*)/remove', api.RemoveTopicHandler),
	('/api/group/(.*)/remove', api.RemoveGroupHandler),
	('/api/group/(.*)/topic/(.*)/update', api.UpdateTopicHandler),
	('/api/group/(.*)/update', api.UpdateGroupHandler),
	('/api/member-autocomplete', api.MemberAutocompleteHandler),
	('/api/remove-vote', api.RemoveVoteHandler),
	('/api/update-user', api.UpdateUser),
	('/api/load-proposal', api.OldLoadProposalHandler),
	('/api/load-votes', api.LoadVotesHandler),
	('/api/load-group-members', api.LoadGroupMembersHandler),
	('/api/group/(.*)/topic/(.*)/participants', api.LoadParticipantsHandler),
	
	# Creation handlers
	('/api/create-group', api.CreateGroupHandler),
	('/api/create-topic', api.CreateTopicHandler),
	('/api/create-proposal', api.CreateProposalHandler),
	('/api/create-vote', api.CreateVoteHandler),
	
	# Notifications handlers
	('/api/group/(.*)/topic/(.*)/notifications', api.TopicNotificationsHandler),
	('/api/group/(.*)/notifications', api.GroupNotificationsHandler),
	('/api/topics-notifications', api.TopicsNotificationsHandler),
	
	('/api/group/(.*)/topic/(.*)/proposal/(.*)', api.LoadProposalHandler),
	('/api/group/(.*)/topic/(.*)', api.LoadTopicHandler),
	('/api/groups', api.LoadGroupsHandler),
	('/api/group/(.*)', api.LoadGroupHandler),
	('/api/user/(.*)', api.LoadUserHandler),
	('/api/create-bug-report', api.CreateBugReportHandler),
	('/api/register', api.RegistrationHandler),
	('/html/topics', html_strips.TopicsHandler),
	('/html/groups', html_strips.GroupsHandler),
	('/html/group/(.*)/topic/(.*)', html_strips.TopicHandler),
	('/html/group/(.*)/members', html_strips.GroupMembersHandler),
	('/html/group/(.*)', html_strips.GroupHandler),
	('/register', RegistrationHandler),
	('/logout', LogoutHandler),
	('/edit-user',EditUserHandler),
], debug=debug, config=config)

app.error_handlers[401] = handle_401
app.error_handlers[404] = handle_404