from google.appengine.ext import db

# Start of Data Model

class BeeVoteUser(db.Model):
	email = db.StringProperty(required=True)

class Group(db.Model):
	name = db.StringProperty(required=True)
	description = db.TextProperty()
	members = db.StringListProperty()

class Topic(db.Model):
	title = db.StringProperty(required=True)
	group = db.ReferenceProperty(Group, required=True)
	description = db.TextProperty()
	activity = db.StringProperty()
	place = db.StringProperty()
	date = db.DateProperty()
	time = db.TimeProperty()
	creator = db.StringProperty()
	img = db.BlobProperty()

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
	
class Vote(db.Model):
	proposal = db.ReferenceProperty(Proposal, required=True)
	creator = db.StringProperty()
	email = db.StringProperty()
	
# End of Data Model