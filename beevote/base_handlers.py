import logging
import os
import traceback

from google.appengine.api.images import Image
from google.appengine.api import users
from google.appengine.ext.webapp import template
import webapp2
from webapp2_extras import sessions

import constants
import language
import models

# List or URLs that you can access without being "registered" in the app
public_urls = ["/", "/logout"]
google_user_urls = ["/", "/logout", "/register"]

def get_template(template_name, template_values={}, navbar_values={}):
    directory = os.path.dirname(__file__)
    basic_head_path = os.path.join(directory, os.path.join('templates', 'basic-head.html'))
    navbar_path = os.path.join(directory, os.path.join('templates', 'navbar.html'))

    user = users.get_current_user()
    if user:
        beevote_user = models.BeeVoteUser.get_from_google_id(user.user_id())
    else:
        beevote_user = None

    if not beevote_user or not beevote_user.language:
        lang_package= 'en'
    else:
        lang_package=beevote_user.language
    
    def_navbar_values = {
        'user': beevote_user,
        'breadcumb': None,
        'feedback_url': constants.feedback_url,
        'lang': language.lang[lang_package],
    }
    def_navbar_values.update(navbar_values)
    
    '''
    breadcumb: {
        previous_elements: [
            {
                title: "",
                href: "",
            },{
                title: "",
                href: "",
            }
        ],
        current_element: {
            title: ""
        }
    }
    '''

    values = {
        'basic_head': template.render(basic_head_path, {}),
        'navbar': template.render(navbar_path, def_navbar_values),
        'lang': language.lang[lang_package],
    }
    
    values.update(template_values)

    path = os.path.join(directory, os.path.join('templates', template_name))
    return template.render(path, values)

def write_template(response, template_name, template_values={}, navbar_values={}):
    response.headers["Pragma"]="no-cache"
    response.headers["Cache-Control"]="no-cache, no-store, must-revalidate, max-age=0, pre-check=0, post-check=0"
    response.headers["Expires"]="Thu, 01 Dec 1994 16:00:00"
    response.out.write(get_template(template_name, template_values, navbar_values))

class BaseHandler(webapp2.RequestHandler):
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

class BaseHtmlHandler(BaseHandler):
    pass

def resize_image(image_data, width, height):
    image = Image(image_data=image_data)
    if (image.width / float(width)) > (image.height / float(height)):
        image.resize(height=height)
        image = Image(image_data=image.execute_transforms())
        x_crop_ratio = (image.width - width) / float(image.width * 2)
        image.crop(x_crop_ratio, 0.0, 1-x_crop_ratio, 1.0)
    else:
        image.resize(width=width)
        image = Image(image_data=image.execute_transforms())
        y_crop_ratio = (image.height - height) / float(image.height * 2)
        image.crop(0.0, y_crop_ratio, 1.0, 1-y_crop_ratio)
    return image.execute_transforms()

class BaseImageHandler(BaseHandler):
    def write_image(self, image, image_name):
        self.response.headers['Content-Type'] = 'image/png'
        self.response.headers['Content-Disposition'] = 'inline; filename="'+image_name+'"'
        width_str = self.request.get('width', None)
        height_str = self.request.get('height', None)
        if width_str is None or height_str is None:
            self.response.out.write(image)
        else:
            try:
                width = int(width_str)
                height = int(height_str)
                self.response.out.write(resize_image(image, width, height))
            except:
                stacktrace = traceback.format_exc()
                logging.error("%s", stacktrace)
                self.response.out.write(image)

class BaseMiscHandler(BaseHandler):
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

class BaseHtmlStripsHandler(BaseHandler):
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

class BaseApiHandler(BaseHandler):
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

class BasicAdminPageHandler(BaseHandler):
    pass