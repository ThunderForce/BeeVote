from google.appengine.api import mail

def send_bug_report_to_admins(report, link):
    mail.send_mail_to_admins(
        sender="BeeVote Bug Report <bug-report@beevote.appspotmail.com>",
        subject="BeeVote bug report received",
        body="""
Dear BeeVote admin,

Your application has received the following bug report:
- ID: {report._id}
- Device: {report.device}
- Browser: {report.browser}
- Description: {report.description}
- Occurrence: {report.occurrence}
- Creation: {report.creation}
- Creator ID: {report.creator}

Follow this link to see all bug reports:
{link}

The BeeVote Team
    """.format(report=report, link=link))

def send_registration_notification(beevote_user, link):
    mail.send_mail(
        sender='BeeVote Registration Notifier <registration-accepted@beevote.appspotmail.com>',
        to=beevote_user.email,
        subject="BeeVote registration request accepted",
        body="""
Dear {beevote_user.name},

Your registration request has been accepted: now you can access BeeVote features!

Follow this link to start:
{link}

Details of registration:
- BeeVote User ID: {beevote_user._id}
- Google User ID: {beevote_user.user_id}
- User email: {beevote_user.email}
- Name: {beevote_user.name}
- Surname: {beevote_user.surname}

The BeeVote Team
    """.format(beevote_user=beevote_user, link=link))

def send_topic_creation_notification(beevote_users, topic, link):
    # TODO
    pass