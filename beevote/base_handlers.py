import os

from google.appengine.ext.webapp import template
from google.appengine.api import users
import webapp2
from webapp2_extras import sessions

import language
import models


# List or URLs that you can access without being "registered" in the app
public_urls = ["/", "/logout"]
google_user_urls = ["/", "/logout", "/register"]

class BaseMiscHandler(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        self.beevote_user = None
        if not self.request.path in public_urls:
            user = users.get_current_user()
            if not user:
                url = request.url
                if request.query_string != "":
                    url += '?' + request.query_string
                self.abort(401, headers={'Location': users.create_login_url(url)})
                #self.redirect(users.create_login_url(url))
                #return
            if not self.request.path in google_user_urls:
                
                self.beevote_user = models.BeeVoteUser.get_from_google_id(user.user_id())
                
                if not self.beevote_user:
                    self.abort(401, headers={'Location': '/register'})
                    return

    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    #@webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()

class BaseHtmlStripsHandler(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        user = users.get_current_user()
        if not user:
            url = request.url
            if request.query_string != "":
                url += '?' + request.query_string
            self.redirect(users.create_login_url(url))
            return
        
        self.beevote_user = models.BeeVoteUser.get_from_google_id(user.user_id())
        
        if not self.beevote_user:
            self.redirect("/register")

    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    #@webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()

class BaseApiHandler(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        
        user = users.get_current_user()
        if user:
            self.beevote_user = models.BeeVoteUser.get_from_google_id(user.user_id())
        else:
            self.beevote_user = None
        
        if not self.beevote_user or not self.beevote_user.language:
            lang_package= 'en'
        else:
            lang_package = self.beevote_user.language
        self.lang = language.lang[lang_package]
        
        '''
        if not self.request.path in public_urls:
            user = users.get_current_user()
            if not user:
                url = request.url
                if request.query_string != "":
                    url += '?' + request.query_string
                self.redirect(users.create_login_url(url))
                return
            self.beevote_user = models.BeeVoteUser.get_from_google_id(user.user_id())
            if not self.beevote_user:
                self.redirect("/register")
        '''
        
        self.response.headers['Content-Type'] = "application/json"

class BasicAdminPageHandler(webapp2.RequestHandler):
    def write_template(self, template_name, template_values={}):
        
        directory = os.path.dirname(__file__)
        basic_head_path = os.path.join(directory, os.path.join('templates', 'basic-head.html'))

        values = {
            'basic_head': template.render(basic_head_path, {}),
        }
        
        values.update(template_values)

        path = os.path.join(directory, os.path.join('templates/admin', template_name))
        self.response.out.write(template.render(path, values))