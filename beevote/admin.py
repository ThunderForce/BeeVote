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

from google.appengine.ext import ndb
import webapp2

import base_handlers
import constants
import emailer
import models

# Start of handlers
class RemoveUserHandler(webapp2.RequestHandler):
	def get(self, user_id):
		beevote_user = models.BeeVoteUser.get_by_id(long(user_id))
		beevote_user.delete()
		self.redirect('/admin/user-manager')

class StatsHandler(base_handlers.BasicAdminPageHandler):
	def get(self):
		duration_24_hours = 24*60*60
		duration_1_week = duration_24_hours*7
		duration_30_days = duration_24_hours*30
		
		groups = ndb.gql("SELECT * FROM Group").fetch(1000)
		groups_created_in_last_30_days = [g for g in groups if (datetime.datetime.now() - g.creation).total_seconds() < (duration_30_days)]
		groups_created_in_last_week = [g for g in groups_created_in_last_30_days if (datetime.datetime.now() - g.creation).total_seconds() < (duration_1_week)]
		groups_created_in_last_24_hours = [g for g in groups_created_in_last_week if (datetime.datetime.now() - g.creation).total_seconds() < (duration_24_hours)]
		
		topics = ndb.gql("SELECT * FROM Topic").fetch(1000)
		topics_created_in_last_30_days = [t for t in topics if (datetime.datetime.now() - t.creation).total_seconds() < (duration_30_days)]
		topics_created_in_last_week = [t for t in topics_created_in_last_30_days if (datetime.datetime.now() - t.creation).total_seconds() < (duration_1_week)]
		topics_created_in_last_24_hours = [t for t in topics_created_in_last_week if (datetime.datetime.now() - t.creation).total_seconds() < (duration_24_hours)]
		
		proposals = ndb.gql("SELECT * FROM Proposal").fetch(1000)
		proposals_created_in_last_30_days = [p for p in proposals if (datetime.datetime.now() - p.creation).total_seconds() < (duration_30_days)]
		proposals_created_in_last_week = [p for p in proposals_created_in_last_30_days if (datetime.datetime.now() - p.creation).total_seconds() < (duration_1_week)]
		proposals_created_in_last_24_hours = [p for p in proposals_created_in_last_week if (datetime.datetime.now() - p.creation).total_seconds() < (duration_24_hours)]
		
		proposal_comments = ndb.gql("SELECT * FROM ProposalComment").fetch(1000)
		proposal_comments_created_in_last_30_days = [c for c in proposal_comments if (datetime.datetime.now() - c.creation).total_seconds() < (duration_30_days)]
		proposal_comments_created_in_last_week = [c for c in proposal_comments_created_in_last_30_days if (datetime.datetime.now() - c.creation).total_seconds() < (duration_1_week)]
		proposal_comments_created_in_last_24_hours = [c for c in proposal_comments_created_in_last_week if (datetime.datetime.now() - c.creation).total_seconds() < (duration_24_hours)]
		
		votes = ndb.gql("SELECT * FROM Vote").fetch(1000)
		
		users = ndb.gql("SELECT * FROM BeeVoteUser").fetch(1000)
		users_registered_in_last_30_days = [u for u in users if u.creation and (datetime.datetime.now() - u.creation).total_seconds() < (duration_30_days)]
		users_registered_in_last_week = [u for u in users_registered_in_last_30_days if u.creation and (datetime.datetime.now() - u.creation).total_seconds() < (duration_1_week)]
		users_registered_in_last_24_hours = [u for u in users_registered_in_last_week if u.creation and (datetime.datetime.now() - u.creation).total_seconds() < (duration_24_hours)]
		users_active_in_last_30_days = [u for u in users if u.last_access and (datetime.datetime.now() - u.last_access).total_seconds() < (duration_30_days)]
		users_active_in_last_week = [u for u in users_active_in_last_30_days if u.last_access and (datetime.datetime.now() - u.last_access).total_seconds() < (duration_1_week)]
		users_active_in_last_24_hours = [u for u in users_active_in_last_week if u.last_access and (datetime.datetime.now() - u.last_access).total_seconds() < (duration_24_hours)]
		
		reports = ndb.gql("SELECT * FROM BugReport").fetch(1000)
		reports_created_in_last_30_days = [r for r in reports if (datetime.datetime.now() - r.creation).total_seconds() < (duration_30_days)]
		reports_created_in_last_week = [r for r in reports_created_in_last_30_days if (datetime.datetime.now() - r.creation).total_seconds() < (duration_1_week)]
		reports_created_in_last_24_hours = [r for r in reports_created_in_last_week if (datetime.datetime.now() - r.creation).total_seconds() < (duration_24_hours)]
		
		base_handlers.write_template(self.response, 'admin/stats.html', {'stats': {
			'number_of_groups': len(groups),
			'groups_created_in_last_24_hours': len(groups_created_in_last_24_hours),
			'groups_created_in_last_week': len(groups_created_in_last_week),
			'groups_created_in_last_30_days': len(groups_created_in_last_30_days),
			'average_members_per_group': sum(len(g.members) for g in groups) / float(len(groups)),
			'number_of_topics': len(topics),
			'topics_created_in_last_24_hours': len(topics_created_in_last_24_hours),
			'topics_created_in_last_week': len(topics_created_in_last_week),
			'topics_created_in_last_30_days': len(topics_created_in_last_30_days),
			'average_topics_per_group': len(topics) / float(len(groups)),
			'number_of_proposals': len(proposals),
			'proposals_created_in_last_24_hours': len(proposals_created_in_last_24_hours),
			'proposals_created_in_last_week': len(proposals_created_in_last_week),
			'proposals_created_in_last_30_days': len(proposals_created_in_last_30_days),
			'average_proposals_per_topic': len(proposals) / float(len(topics)),
			'number_of_proposal_comments': len(proposal_comments),
			'proposal_comments_created_in_last_24_hours': len(proposal_comments_created_in_last_24_hours),
			'proposal_comments_created_in_last_week': len(proposal_comments_created_in_last_week),
			'proposal_comments_created_in_last_30_days': len(proposal_comments_created_in_last_30_days),
			'number_of_users': len(users),
			'users_by_language': {
				'en': len([u for u in users if (u.language is None) or (u.language == 'en')]),
				'it': len([u for u in users if u.language == 'it']),
			},
			'users_registered_in_last_24_hours': len(users_registered_in_last_24_hours),
			'users_registered_in_last_week': len(users_registered_in_last_week),
			'users_registered_in_last_30_days': len(users_registered_in_last_30_days),
			'users_active_in_last_24_hours': len(users_active_in_last_24_hours),
			'users_active_in_last_week': len(users_active_in_last_week),
			'users_active_in_last_30_days': len(users_active_in_last_30_days),
			'number_of_reports': len(reports),
			'reports_created_in_last_24_hours': len(reports_created_in_last_24_hours),
			'reports_created_in_last_week': len(reports_created_in_last_week),
			'reports_created_in_last_30_days': len(reports_created_in_last_30_days),
			'number_of_votes': len(votes),
		}})

class UserManagerHandler(base_handlers.BasicAdminPageHandler):
	def get(self):
		sort_param = self.request.get("sort")
		if sort_param == "creation":
			users = ndb.gql("SELECT * FROM BeeVoteUser ORDER BY creation DESC")
		elif sort_param == "last_access":
			users = ndb.gql("SELECT * FROM BeeVoteUser ORDER BY last_access DESC")
		elif sort_param == "email":
			users = ndb.gql("SELECT * FROM BeeVoteUser ORDER BY email ASC")
		elif sort_param == "language":
			users = ndb.gql("SELECT * FROM BeeVoteUser ORDER BY language ASC")
		else:
			users = ndb.gql("SELECT * FROM BeeVoteUser")
		base_handlers.write_template(self.response, 'admin/user-manager.html', {'users': users})

class BugReportsHandler(base_handlers.BasicAdminPageHandler):
	def get(self):
		reports = ndb.gql("SELECT * FROM BugReport")
		base_handlers.write_template(self.response, 'admin/bug-reports.html', {'reports': reports})

class FeatureChangesHandler(base_handlers.BasicAdminPageHandler):
	def get(self):
		feature_changes = ndb.gql("SELECT * FROM FeatureChange").fetch(1000)
		feature_changes = sorted(feature_changes, key=lambda feature: feature.creation, reverse=True)
		base_handlers.write_template(self.response, 'admin/feature-changes.html', {'feature_changes': feature_changes})

class AddFeatureChangeHandler(base_handlers.BasicAdminPageHandler):
	def post(self):
		description = self.request.get('description')
		feature = models.FeatureChange(
			description=description,
		)
		feature.put()
		self.redirect('/admin/feature-changes')

class SendMailHandler(base_handlers.BasicAdminPageHandler):
	def post(self):
		to = self.request.get('to')
		from_name = self.request.get('from-name')
		from_address = self.request.get('from-address')
		sender = from_name+" <"+from_address+"@beevote.appspotmail.com>"
		subject = self.request.get('subject')
		body = self.request.get('body')
		html = body
		result = emailer._send_mail_to_user(
			sender=sender,
			to=to,
			subject=subject,
			html=html,
			body=body,
		)
		if result:
			self.response.out.write("Email sent successfully.")
		else:
			self.response.out.write("Error while sending email.")

class EmailerHandler(base_handlers.BasicAdminPageHandler):
	def get(self):
		base_handlers.write_template(self.response, 'admin/emailer.html', {})

class AdminMenuHandler(base_handlers.BasicAdminPageHandler):
	def get(self):
		base_handlers.write_template(self.response, 'admin/admin-menu.html', {})

# End of handlers

app = webapp2.WSGIApplication([
	('/admin/remove-user/(.*)', RemoveUserHandler),
	('/admin/stats', StatsHandler),
	('/admin/user-manager', UserManagerHandler),
	('/admin/bug-reports', BugReportsHandler),
	('/admin/feature-changes', FeatureChangesHandler),
	('/admin/add-feature-change', AddFeatureChangeHandler),
	('/admin/ajax/send-email', SendMailHandler),
	('/admin/emailer', EmailerHandler),
	('/admin/home', AdminMenuHandler)
], debug=True, config=constants.wsgiapplication_config)
