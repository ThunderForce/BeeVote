from google.appengine.ext import db

# Start of Data Model

class BeeVoteUser(db.Model):
	name = db.StringProperty()
	surname = db.StringProperty()
	user_id = db.StringProperty()
	email = db.StringProperty(required=True)

class Group(db.Model):
	name = db.StringProperty(required=True)
	description = db.TextProperty()
	members = db.StringListProperty()
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
	creator = db.StringProperty()
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
	creator = db.StringProperty()
	email = db.StringProperty()
	creation = db.DateTimeProperty(auto_now_add=True)
	
class Vote(db.Model):
	proposal = db.ReferenceProperty(Proposal, required=True)
	creator = db.StringProperty()
	email = db.StringProperty()
	
# End of Data Model