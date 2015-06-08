import datetime

from google.appengine.api import users
import webapp2

import base_handlers
import models

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