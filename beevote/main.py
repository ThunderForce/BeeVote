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
import image_handlers

from google.appengine.api import users
import webapp2

import api
import base_handlers
import html_strips
import models


# Start of handlers

class MainHandler(base_handlers.BaseMiscHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			if not self.beevote_user and not models.BeeVoteUser.get_from_google_id(user.user_id()):
				self.redirect("/register")
				return
			else:
				self.redirect('/home')
		else:
			values = {
				'login_url': users.create_login_url('/home'),
			}
			base_handlers.write_template(self.response, 'index.html', values)

class HomeHandler(base_handlers.BaseMiscHandler):
	def get(self, group_id, topic_id):
		
		if not self.beevote_user:
			self.redirect("/register")
			return
		
		last_access = self.beevote_user.last_access if hasattr(self.beevote_user, 'last_access') else datetime.datetime.min
		self.beevote_user.last_access = datetime.datetime.now()
		self.beevote_user.put()
		
		feature_changes = models.FeatureChange.get_from_date(last_access)
		
		values = {
			'user' : self.beevote_user,
			'feature_changes': feature_changes,
			'group_id': group_id,
			'topic_id': topic_id,
		}
		base_handlers.write_template(self.response, 'groups-layout.html',values)

class ProfileHandler(base_handlers.BaseMiscHandler):
	def get(self, user_id):
		# TODO Use user_id to get user and put it in values
		values = {}
		base_handlers.write_template(self.response, 'user-profile.html', values)

class RegistrationHandler(base_handlers.BaseMiscHandler):
	def get(self):
		user_id = users.get_current_user().user_id()
		if self.beevote_user or models.BeeVoteUser.get_from_google_id(user_id):
			self.redirect("/")
			return
		base_handlers.write_template(self.response, 'registration-form.html', {})

class ReportBugHandler(base_handlers.BaseMiscHandler):
	def get(self):
		values = {}
		base_handlers.write_template(self.response, 'report-bug.html', values)

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
	base_handlers.write_template(response, 'errors/401.html', {'detail': exception.detail})

def handle_404(request, response, exception):
	response.set_status(404)
	base_handlers.write_template(response, 'not_found.html', {'url': request.path})

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
	# Home handlers
	('/', MainHandler),
	webapp2.Route('/group/<group_id:\d+>/topic/<topic_id:\d+>', handler=HomeHandler),
	webapp2.Route('/group/<group_id:\d+>', handler=HomeHandler, defaults={'topic_id': None}),
	webapp2.Route('/home', handler=HomeHandler, defaults={'group_id': None, 'topic_id': None}),
	
	# Images handlers
	('/user/(\d+)/image', image_handlers.UserImageHandler),
	('/group/(\d+)/topic/(\d+)/image', image_handlers.TopicImageHandler),
	('/group/(\d+)/image', image_handlers.GroupImageHandler),
	
	# Creation handlers
	('/api/create-group', api.CreateGroupHandler),
	('/api/create-topic', api.CreateTopicHandler),
	('/api/create-proposal', api.CreateProposalHandler),
	('/api/create-vote', api.CreateVoteHandler),
	
	# Updating handlers
	('/api/update-user', api.UpdateUser),
	('/api/group/(\d+)/topic/(\d+)/update', api.UpdateTopicHandler),
	('/api/group/(\d+)/topic/(\d+)/update-personal-settings', api.UpdateTopicPersonalSettingsHandler),
	('/api/group/(\d+)/update-personal-settings', api.UpdateGroupPersonalSettingsHandler),
	
	# Removal handlers
	('/api/group/(\d+)/remove', api.RemoveGroupHandler),
	('/api/group/(\d+)/topic/(\d+)/remove-participation', api.RemoveParticipationHandler),
	('/api/group/(\d+)/topic/(\d+)/proposal/(\d+)/remove', api.RemoveProposalHandler),
	('/api/group/(\d+)/members/remove', api.RemoveGroupMemberHandler),
	('/api/group/(\d+)/topic/(\d+)/remove', api.RemoveTopicHandler),
	('/api/remove-vote', api.RemoveVoteHandler),
	
	# Notifications handlers
	('/api/group/(\d+)/topic/(\d+)/notifications', api.TopicNotificationsHandler),
	('/api/group/(\d+)/notifications', api.GroupNotificationsHandler),
	('/api/topics-notifications', api.TopicsNotificationsHandler),
	
	# Other API handlers
	('/api/group/(\d+)/members/add', api.AddGroupMemberHandler),
	('/api/group/(\d+)/topic/(\d+)/add-participation', api.AddParticipationHandler),
	('/api/group/(\d+)/update', api.UpdateGroupHandler),
	('/api/member-autocomplete', api.MemberAutocompleteHandler),
	('/api/load-proposal', api.OldLoadProposalHandler),
	('/api/load-votes', api.LoadVotesHandler),
	('/api/load-group-members', api.LoadGroupMembersHandler),
	('/api/group/(\d+)/topic/(\d+)/participants', api.LoadParticipantsHandler),
	('/api/group/(\d+)/topic/(\d+)/proposal/(\d+)/add-comment', api.CreateProposalCommentHandler),
	('/api/group/(\d+)/topic/(\d+)/proposal/(\d+)', api.LoadProposalHandler),
	('/api/group/(\d+)/topic/(\d+)', api.LoadTopicHandler),
	('/api/groups', api.LoadGroupsHandler),
	('/api/group/(\d+)', api.LoadGroupHandler),
	('/api/user/(\d+)', api.LoadUserHandler),
	('/api/create-bug-report', api.CreateBugReportHandler),
	('/api/register', api.RegistrationHandler),
	
	# HTML strips handlers
	('/html/topics', html_strips.TopicsHandler),
	('/html/groups', html_strips.GroupsHandler),
	('/html/group/(\d+)/topic/(\d+)', html_strips.TopicHandler),
	('/html/group/(\d+)/members', html_strips.GroupMembersHandler),
	('/html/group/(\d+)', html_strips.GroupHandler),
	
	# Other handlers
	('/profile/(\d+)', ProfileHandler),
	('/report-bug', ReportBugHandler),
	('/register', RegistrationHandler),
	('/logout', LogoutHandler),
], debug=debug, config=config)

app.error_handlers[401] = handle_401
app.error_handlers[404] = handle_404