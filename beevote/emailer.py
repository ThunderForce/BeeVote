import logging
import os

from google.appengine.api import mail
from google.appengine.ext.webapp import template
from google.appengine.runtime import apiproxy_errors

import language

def _get_email_body(template_name, lang_package, template_values):
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, os.path.join('templates/email', template_name))
    template_values.update({'lang': language.lang[lang_package]})
    rendered_template = template.render(path, template_values)
    return rendered_template

def _get_email_content(body_template, lang_package, template_values):
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, os.path.join('templates/email', 'basic-template.html'))
    rendered_template = template.render(path, {
        'lang': language.lang[lang_package],
        'email_body_table': _get_email_body(body_template, lang_package, template_values)
    })
    return rendered_template

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

def _send_mail_to_user(sender, to, subject, html, body):
    try:
        message = mail.EmailMessage(
            sender=sender,
            to=to,
            subject=subject,
            body=body,
            html=html
        )
        message.send()
        return True
    except apiproxy_errors.OverQuotaError, message:
        logging.error(message)
        return False

def send_bug_report_to_admins(report, link):
    return _send_mail_to_admins(
        sender="Beevote Bug Report <bug-report@beevote.appspotmail.com>",
        subject="Beevote bug report received",
        body="""
Dear Beevote admin,

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

The Beevote Team
    """.format(report=report, link=link))

def send_registration_notification(beevote_user, lang_code, link):
    return _send_mail_to_user(
        sender='Beevote registration notifier <registration-successful@beevote.appspotmail.com>',
        to=beevote_user.email,
        subject=language.lang[lang_code]['email']['registration']['subject'],
        body=language.lang[lang_code]['email']['registration']['body'].format(beevote_user_name=beevote_user.name, beevote_user_surname=beevote_user.surname, beevote_user_email=beevote_user.email, link=link),
        html=_get_email_content("registration-notification.html", lang_code, {
            'beevote_user_id': beevote_user.key.id(),
            'beevote_user_name': beevote_user.name,
            'beevote_user_surname': beevote_user.surname,
            'beevote_user_email': beevote_user.email,
            'link': link
        })
    ) 
def send_proposal_creation_email(beevote_user, lang_code, proposal, link):
    return _send_mail_to_user(
        sender='Beevote proposal creation notifier <new-proposal-notification@beevote.appspotmail.com>',
        to=beevote_user.email,
        subject=language.lang[lang_code]['email']['proposal_creation']['subject'],
        body=language.lang[lang_code]['email']['proposal_creation']['body'].format(beevote_user_name=beevote_user.name, group_name=proposal.topic.get().group.get().name, topic_title=proposal.topic.get().title, proposal_title=proposal.title, link=link),
        html=_get_email_content("proposal-creation.html", lang_code, {
            'beevote_user_name': beevote_user.name,
            'group_name': proposal.topic.get().group.get().name,
            'topic_title': proposal.topic.get().title,
            'proposal_title': proposal.title,
            'link': link
        })
    )
    
def send_topic_creation_email(beevote_user, lang_code, topic, link):
    return _send_mail_to_user(
        sender='Beevote topic creation notifier <new-topic-notification@beevote.appspotmail.com>',
        to=beevote_user.email,
        subject=language.lang[lang_code]['email']['topic_creation']['subject'],
        body=language.lang[lang_code]['email']['topic_creation']['body'].format(beevote_user_name=beevote_user.name, group_name=topic.group.get().name, topic_title=topic.title, link=link),
        html=_get_email_content("topic-creation.html", lang_code, {
            'beevote_user_name': beevote_user.name,
            'group_name': topic.group.get().name,
            'topic_title': topic.title,
            'link': link
        })
    )