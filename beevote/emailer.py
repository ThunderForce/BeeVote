import logging

from google.appengine.api import mail
from google.appengine.runtime import apiproxy_errors

import language

def _send_mail_to_admins(sender, subject, body):
    try:
        mail.send_mail_to_admins(
            sender=sender,
            subject=subject,
            body=body,
        )
        return True
    except apiproxy_errors.OverQuotaError, message:
        logging.error(message)
        return False
    pass

def _send_mail_to_user(sender, to, subject, body):
    try:
        mail.send_mail(
            sender=sender,
            to=to,
            subject=subject,
            body=body,
        )
        return True
    except apiproxy_errors.OverQuotaError, message:
        logging.error(message)
        return False

def send_bug_report_to_admins(report, link):
    return _send_mail_to_admins(
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
    return _send_mail_to_user(
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

def send_proposal_creation_email(beevote_user, lang_code, proposal, link):
    return _send_mail_to_user(
        sender='BeeVote proposal creation notifier <new-proposal-notification@beevote.appspotmail.com>',
        to=beevote_user.email,
        subject=language.lang[lang_code]['email']['proposal_creation']['subject'],
        body=language.lang[lang_code]['email']['proposal_creation']['body'].format(beevote_user_name=beevote_user.name, group_name=proposal.topic.get().group.get().name, topic_title=proposal.topic.get().title, proposal_title=proposal.title, link=link))
    
def send_topic_creation_email(beevote_user, lang_code, topic, link):
    return _send_mail_to_user(
        sender='BeeVote topic creation notifier <new-topic-notification@beevote.appspotmail.com>',
        to=beevote_user.email,
        subject=language.lang[lang_code]['email']['topic_creation']['subject'],
        body=language.lang[lang_code]['email']['topic_creation']['body'].format(beevote_user_name=beevote_user.name, group_name=topic.group.get().name, topic_title=topic.title, link=link))