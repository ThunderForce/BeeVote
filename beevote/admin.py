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

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
import webapp2

import models


#import json
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
		beevote_user = models.BeeVoteUser.get_by_id(long(user_id))
		beevote_user.delete()
		self.redirect('/admin/user-manager')

class UserManagerHandler(BasicPageHandler):
	def get(self):
		users = ndb.gql("SELECT * FROM BeeVoteUser")
		self.write_template('user-manager.html', {'users': users})

class BugReportsHandler(BasicPageHandler):
	def get(self):
		reports = ndb.gql("SELECT * FROM BugReport")
		self.write_template('bug-reports.html', {'reports': reports})

class FeatureChangesHandler(BasicPageHandler):
	def get(self):
		feature_changes = ndb.gql("SELECT * FROM FeatureChange").fetch(1000)
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

class AdminMenuHandler(BasicPageHandler):
	def get(self):
		self.write_template('admin-menu.html', {})

# End of handlers

app = webapp2.WSGIApplication([
	('/admin/remove-user/(.*)', RemoveUserHandler),
	('/admin/user-manager', UserManagerHandler),
	('/admin/bug-reports', BugReportsHandler),
	('/admin/feature-changes', FeatureChangesHandler),
	('/admin/add-feature-change', AddFeatureChangeHandler),
	('/admin/home', AdminMenuHandler)
], debug=True)
