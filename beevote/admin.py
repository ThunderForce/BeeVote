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
		basic_head_path = os.path.join(directory, os.path.join('templates', 'basic-head.html'))

		user = users.get_current_user()

		val_user = {
			'user': user,
		}

		values = {
			'basic_head': template.render(basic_head_path, {}),
		}
		
		values.update(template_values)

		path = os.path.join(directory, os.path.join('templates/admin', template_name))
		self.response.out.write(template.render(path, values))

class AllowedUsersPageHandler(BasicPageHandler):
	def get(self):
		allowed_users = db.GqlQuery("SELECT * FROM BeeVoteUser")
		self.write_template('allowed-users.html', {'allowed_users': allowed_users})

class AddUserHandler(webapp2.RequestHandler):
	def post(self):
		email = self.request.get("email")
		beevote_user = models.BeeVoteUser(email = email)
		beevote_user.put()
		self.redirect('/admin/allowed-users')

class RemoveUserHandler(webapp2.RequestHandler):
	def get(self, user_id):
		beevote_user_key = db.Key.from_path('BeeVoteUser', long(user_id))
		beevote_user = db.get(beevote_user_key)
		beevote_user.delete()
		self.redirect('/admin/allowed-users')

class NotFoundPageHandler(BasicPageHandler):
	def get(self):
		self.error(404)
		self.write_template('not_found.html', {'url': self.request.path})

# End of handlers

app = webapp2.WSGIApplication([
	('/admin/user/add', AddUserHandler),
	('/admin/user/remove/(.*)', RemoveUserHandler),
	('/admin/allowed-users', AllowedUsersPageHandler),
	('/.*', NotFoundPageHandler)
], debug=True)
