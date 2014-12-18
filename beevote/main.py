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
from google.appengine.ext import db
from google.appengine.ext.webapp import template

# Start of Data Model

class Topic(db.Model):
	title = db.StringProperty(required=True)
	description = db.TextProperty()
	activity = db.StringProperty()
	place = db.StringProperty()
	date = db.DateProperty()
	time = db.TimeProperty()
	creator = db.StringProperty()

class Suggestion(db.Model):
	title = db.StringProperty(required=True)
	topic = db.ReferenceProperty(Topic, required=True)
	activity = db.StringProperty()
	place = db.StringProperty()
	date = db.DateProperty()
	time = db.TimeProperty()
	creator = db.StringProperty()
	
class Vote(db.Model):
	suggestion = db.ReferenceProperty(Suggestion, required=True)
	
# End of Data Model

# Start of handlers

class MainHandler(webapp2.RequestHandler):
	def get(self):
		values = {}
		directory = os.path.dirname(__file__)
		path = os.path.join(directory, os.path.join('templates', 'index.html'))
		self.response.out.write(template.render(path, values))

class TopicSampleHandler(webapp2.RequestHandler):
	def get(self):
		values = {}
		directory = os.path.dirname(__file__)
		path = os.path.join(directory, os.path.join('templates', 'topic-layout.html'))
		self.response.out.write(template.render(path, values))

class NotFoundPageHandler(webapp2.RequestHandler):
	def get(self):
		self.error(404)
		values = {}
		directory = os.path.dirname(__file__)
		path = os.path.join(directory, os.path.join('templates', 'not_found.html'))
		self.response.out.write(template.render(path, values))

# End of handlers

app = webapp2.WSGIApplication([
	('/', MainHandler),
	('/topic-sample', TopicSampleHandler),
	('/.*', NotFoundPageHandler)
], debug=True)
