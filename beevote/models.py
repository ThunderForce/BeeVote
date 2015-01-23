from google.appengine.ext import db

# Start of Data Model

class BeeVoteUser(db.Model):
	name = db.StringProperty()
	surname = db.StringProperty()
	user_id = db.StringProperty()
	email = db.StringProperty(required=True)
	creation = db.DateTimeProperty(auto_now_add=True)
	img = db.BlobProperty()

class RegistrationRequest(db.Model):
	user_id = db.StringProperty()
	email = db.StringProperty()
	name = db.StringProperty()
	surname = db.StringProperty()
	creation = db.DateTimeProperty(auto_now_add=True)

class Group(db.Model):
	name = db.StringProperty(required=True)
	description = db.TextProperty()
	members = db.ListProperty(db.Key) # BeeVoteUser Key
	creator = db.ReferenceProperty(BeeVoteUser, required=True)
	creation = db.DateTimeProperty(auto_now_add=True)

class Topic(db.Model):
	title = db.StringProperty(required=True)
	group = db.ReferenceProperty(Group, required=True)
	description = db.TextProperty()
	activity = db.StringProperty()
	place = db.StringProperty()
	date = db.DateProperty()
	time = db.TimeProperty()
	deadline = db.DateTimeProperty()
	creator = db.ReferenceProperty(BeeVoteUser, required=True)
	img = db.BlobProperty()
	creation = db.DateTimeProperty(auto_now_add=True)

class Proposal(db.Model):
	title = db.StringProperty(required=True)
	topic = db.ReferenceProperty(Topic, required=True)
	description = db.TextProperty()
	activity = db.StringProperty()
	place = db.StringProperty()
	date = db.DateProperty()
	time = db.TimeProperty()
	creator = db.ReferenceProperty(BeeVoteUser, required=True)
	creation = db.DateTimeProperty(auto_now_add=True)
	
class Vote(db.Model):
	proposal = db.ReferenceProperty(Proposal, required=True)
	creator = db.ReferenceProperty(BeeVoteUser, required=True)
	
# End of Data Model

# Start of functions

def get_beevote_user_from_google_id(user_id):
	return db.GqlQuery('SELECT * FROM BeeVoteUser WHERE user_id = :1', user_id).get()

def get_registration_request_from_google_id(user_id):
	return db.GqlQuery('SELECT * FROM RegistrationRequest WHERE user_id = :1', user_id).get()

# End of functions