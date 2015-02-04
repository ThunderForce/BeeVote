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
import datetime
from datetime import timedelta
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import users

from google.appengine.api import mail

import models
import api
import time

# Start of handlers

def write_template(response, template_name, template_values={}):
	directory = os.path.dirname(__file__)
	path = os.path.join(directory, os.path.join('templates', template_name))
	rendered_template = template.render(path, template_values)
	response.headers["Pragma"]="no-cache"
	response.headers["Cache-Control"]="no-cache, no-store, must-revalidate, pre-check=0, post-check=0"
	response.headers["Expires"]="Thu, 01 Dec 1994 16:00:00"
	response.out.write(rendered_template)

def is_user_in_group(beevote_user, group):
	if group.members == [] or beevote_user.key() in group.members:
		return True
	else:
		return False

class BaseHandler(webapp2.RequestHandler):
	def __init__(self, request, response):
		self.initialize(request, response)
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

class GroupsHandler(BaseHandler):
	def get(self):
		
		time.sleep(0.5)

		user = users.get_current_user()
		beevote_user = models.get_beevote_user_from_google_id(user.user_id())
		
		groups = db.GqlQuery("SELECT * FROM Group").fetch(1000)
		
		groups = [g for g in groups if not (not beevote_user.key() in g.members) and (g.members != [])]
		
		for group in groups:
			
			if len(group.name) > 20:
				group.name_short = group.name[:16]
		
		values = {
			'groups' : groups,
		}
		write_template(self.response, 'html/groups.html',values)