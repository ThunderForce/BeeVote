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

# Start of Data Model

class Topic(db.Model):
	title = db.StringProperty(required=True)
	description = db.TextProperty()
	activity = db.StringProperty()
	place = db.StringProperty()
	date = db.DateProperty()
	time = db.TimeProperty()
	creator = db.StringProperty()

class Proposal(db.Model):
	title = db.StringProperty(required=True)
	topic = db.ReferenceProperty(Topic, required=True)
	activity = db.StringProperty()
	place = db.StringProperty()
	date = db.DateProperty()
	time = db.TimeProperty()
	creator = db.StringProperty()
	
class Vote(db.Model):
	proposal = db.ReferenceProperty(Proposal, required=True)
	
# End of Data Model

# Start of filling dummy data

topic_stasera = Topic(
	key_name = "1",
	title = "Che facciamo stasera?",
	description = "Dobbiamo decidere che fare stasera perche' mi annoio",
	date = datetime.date(2014,12,18),
	time = datetime.time(21, 0),
	creator = "Riccardo",
)
topic_stasera.put()

topic_cena = Topic(
	key_name = "2",
	title = "Cena dei 100 giorni!",
	description = "Festeggiamo i 100 giorni! (possibilmente dove si spende poco)",
	activity = "Cena",
	creator = "Alessandro",
)
topic_cena.put()

topic_film = Topic(
	key_name = "3",
	title = "Dove vediamo Interstellar!",
	description = "Dobbiamo decidere un giorno per andare a vedere questo fantastico film!",
	activity = "Visione film Interstellar",
	place = "Cinema",
	creator = "Luigi",
)
topic_film.put()

suggestion_stasera_film = Proposal(
	key_name = "4",
	title = "Andiamo a vedere Interstellar!",
	topic = topic_stasera,
	activity = "Visione film Interstellar",
	place = "UCI Cinema Parco Leonardo",
	creator = "Luigi",
)
suggestion_stasera_film.put()

suggestion_stasera_cena = Proposal(
	key_name = "5",
	title = "Facciamo una cena tutti insieme!",
	topic = topic_stasera,
	activity = "Cena di gruppo",
	place = "Casa di Alessandro",
	creator = "Alessandro",
)
suggestion_stasera_cena.put()



# End of filling dummy data

# Start of handlers

class BasicPageHandler(webapp2.RequestHandler):
	def write_template(self, template_name, template_values={}):
	
		directory = os.path.dirname(__file__)
		import_path = os.path.join(directory, os.path.join('templates', 'basic-head.html'))
	
		values = {
			'basic_head': template.render(import_path, {}),
		}
		
		values.update(template_values)

		path = os.path.join(directory, os.path.join('templates', template_name))
		self.response.out.write(template.render(path, values))

class MainHandler(BasicPageHandler):
	def get(self):
		self.write_template('index.html')

class TopicSampleHandler(BasicPageHandler):
	def get(self):
		self.write_template('topic-layout.html')

class GroupListHandler(BasicPageHandler):
	def get(self):
		self.write_template('groups-list-layout.html')

class GroupHandler(BasicPageHandler):
	def get(self):
		topics = db.GqlQuery('SELECT * FROM Topic').fetch(10)
		values = {'topics': topics}
		self.write_template('topics-layout.html', values)

class ProposalHandler(BasicPageHandler):
	def get(self):
		self.write_template('proposal-layout.html')

class NewTopicHandler(BasicPageHandler):
	def get(self):
		self.write_template('topic-form.html')
		
class NewProposalHandler(BasicPageHandler):
	def get(self):
		self.write_template('proposal-form.html')

class CreateTopicHandler(BasicPageHandler):
	def post(self):
		title = self.request.get('inputTopicName')
		what = self.request.get('inputWhat')
		where= self.request.get('inputWhere')
		date = self.request.get('inputDate')
		time = self.request.get('inputTime')
		topic = Topic(title=title)
		topic.activity = what
		topic.place = where
		topic.date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
		topic.time = datetime.datetime.strptime(time, '%H:%M').time()
		topic.put()
		self.redirect('/group')

class CreateProposalHandler(BasicPageHandler):
	def post(self):
		title = self.request.get('inputProposalName')
		what = self.request.get('inputWhat')
		where= self.request.get('inputWhere')
		date = self.request.get('inputDate')
		time = self.request.get('inputTime')
		topic_key = db.Key.from_path('Topic', '1')
		topic = db.get(topic_key)
		proposal = Proposal(
			title=title,
			topic=topic,
		)
		proposal.activity = what
		proposal.place = where
		if date != "":
			proposal.date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
		if time != "":
			proposal.time = datetime.datetime.strptime(time, '%H:%M').time()
		proposal.put()
		self.redirect('/')

class NotFoundPageHandler(BasicPageHandler):
	def get(self):
		self.error(404)
		self.write_template('not_found.html', {'url': self.request.path})

# End of handlers

app = webapp2.WSGIApplication([
	('/', MainHandler),
	('/topic-sample', TopicSampleHandler),
	('/groups', GroupListHandler),
	('/group', GroupHandler),
	('/proposal', ProposalHandler),
	('/new-topic', NewTopicHandler),
	('/new-proposal', NewProposalHandler),
	('/create-topic', CreateTopicHandler),
	('/create-proposal', CreateProposalHandler),
	('/.*', NotFoundPageHandler)
], debug=True)
