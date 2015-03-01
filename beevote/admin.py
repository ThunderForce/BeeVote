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
#import json
from google.appengine.ext import db
from google.appengine.ext.webapp import template

from google.appengine.api import mail

import models

import datetime

# Start of handlers

class BasicPageHandler(webapp2.RequestHandler):
	def write_template(self, template_name, template_values={}):
		
		directory = os.path.dirname(__file__)
		basic_head_path = os.path.join(directory, os.path.join('templates', 'basic-head.html'))

		values = {
			'basic_head': template.render(basic_head_path, {}),
		}
		
		values.update(template_values)

		path = os.path.join(directory, os.path.join('templates/admin', template_name))
		self.response.out.write(template.render(path, values))

class RemoveUserHandler(webapp2.RequestHandler):
	def get(self, user_id):
		beevote_user_key = db.Key.from_path('BeeVoteUser', long(user_id))
		beevote_user = db.get(beevote_user_key)
		beevote_user.delete()
		self.redirect('/admin/user-manager')

class UserManagerHandler(BasicPageHandler):
	def get(self):
		requests = db.GqlQuery("SELECT * FROM RegistrationRequest")
		users = db.GqlQuery("SELECT * FROM BeeVoteUser")
		self.write_template('user-manager.html', {'requests': requests, 'users': users})

class BugReportsHandler(BasicPageHandler):
	def get(self):
		reports = db.GqlQuery("SELECT * FROM BugReport")
		self.write_template('bug-reports.html', {'reports': reports})

class FeatureChangesHandler(BasicPageHandler):
	def get(self):
		feature_changes = db.GqlQuery("SELECT * FROM FeatureChange").fetch(1000)
		feature_changes = sorted(feature_changes, key=lambda feature: feature.creation, reverse=True)
		self.write_template('feature-changes.html', {'feature_changes': feature_changes})

class AddFeatureChangeHandler(BasicPageHandler):
	def post(self):
		description = self.request.get('description')
		feature = models.FeatureChange(
			description=description,
		)
		feature.put()
		self.redirect('/admin/feature-changes')

class AcceptRegistrationRequestHandler(webapp2.RequestHandler):
	def get(self, request_id):
		request_key = db.Key.from_path('RegistrationRequest', long(request_id))
		request = db.get(request_key)
		beevote_user = models.BeeVoteUser(
			user_id = request.user_id,
			email = request.email,
			name = request.name,
			surname = request.surname
		)
		
		beevote_user.last_access = datetime.datetime.now()
		
		beevote_user.put()
		request.delete()
		
		mail.send_mail(
			sender='BeeVote Registration Notifier <registration-accepted@beevote.appspotmail.com>',
			to=request.email,
			subject="BeeVote registration request accepted",
			body="""
Dear {request.name} {request.surname},

Your registration request has been accepted: now you can access BeeVote features!

Follow this link to start:
{link}

Details of registration request:
- User ID: {request.user_id}
- User email: {request.email}
- Name: {request.name}
- Surname: {request.surname}

The BeeVote Team
""".format(request=request, link=self.request.host))
		
		self.redirect('/admin/user-manager')

# End of handlers

app = webapp2.WSGIApplication([
	('/admin/remove-user/(.*)', RemoveUserHandler),
	('/admin/user-manager', UserManagerHandler),
	('/admin/bug-reports', BugReportsHandler),
	('/admin/feature-changes', FeatureChangesHandler),
	('/admin/add-feature-change', AddFeatureChangeHandler),
	('/admin/accept-request/(.*)', AcceptRegistrationRequestHandler)
], debug=True)
