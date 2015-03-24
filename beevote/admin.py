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

class StatsHandler(BasicPageHandler):
	def get(self):
		groups = ndb.gql("SELECT * FROM Group").fetch(1000)
		topics = ndb.gql("SELECT * FROM Topic").fetch(1000)
		users = ndb.gql("SELECT * FROM BeeVoteUser").fetch(1000)
		users_active_in_last_24_hours = [u for u in users if u.last_access and (datetime.datetime.now() - u.last_access).total_seconds() < (24*60*60)]
		users_active_in_last_week = [u for u in users if u.last_access and (datetime.datetime.now() - u.last_access).total_seconds() < (7*24*60*60)]
		users_active_in_last_30_days = [u for u in users if u.last_access and (datetime.datetime.now() - u.last_access).total_seconds() < (30*24*60*60)]
		self.write_template('stats.html', {'stats': {
			'number_of_groups': len(groups),
			'average_members_per_group': sum(len(g.members) for g in groups) / float(len(groups)),
			'number_of_topics': len(topics),
			'average_topics_per_group': len(topics) / float(len(groups)),
			'number_of_users': len(users),
			'users_active_in_last_24_hours': len(users_active_in_last_24_hours),
			'users_active_in_last_week': len(users_active_in_last_week),
			'users_active_in_last_30_days': len(users_active_in_last_30_days),
		}})

class UserManagerHandler(BasicPageHandler):
	def get(self):
		sort_param = self.request.get("sort")
		if sort_param == "creation":
			users = ndb.gql("SELECT * FROM BeeVoteUser ORDER BY creation DESC")
		elif sort_param == "last_access":
			users = ndb.gql("SELECT * FROM BeeVoteUser ORDER BY last_access DESC")
		else:
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
	('/admin/stats', StatsHandler),
	('/admin/user-manager', UserManagerHandler),
	('/admin/bug-reports', BugReportsHandler),
	('/admin/feature-changes', FeatureChangesHandler),
	('/admin/add-feature-change', AddFeatureChangeHandler),
	('/admin/home', AdminMenuHandler)
], debug=True)
