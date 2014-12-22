from google.appengine.ext import db

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
	description = db.TextProperty()
	activity = db.StringProperty()
	place = db.StringProperty()
	date = db.DateProperty()
	time = db.TimeProperty()
	creator = db.StringProperty()
	
class Vote(db.Model):
	proposal = db.ReferenceProperty(Proposal, required=True)
	creator = db.StringProperty()
	
# End of Data Model