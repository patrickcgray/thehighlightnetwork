import os
import webapp2
import jinja2
import json
import datetime
import logging

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch

urlfetch.set_default_fetch_deadline(60)

#initalize the jinja2 template
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)
#I need this Jinja2 filter to be able to pass variables into the templaes and use them in Javascript
jinja_env.filters['json_encode'] = json.dumps

#I use this to only select from the past couple days of posts
def hours_ago(time_h):
    return datetime.datetime.now() - datetime.timedelta(hours=time_h)


from pagehandlers import otherhandlers
from pagehandlers import profilehandlers
from pagehandlers import basehandler
from pagehandlers import videohandlers

#Web2App Extras config needed by SimpleAuth
config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'my-super-secret-key',
}

def handle_404(request, response, exception):
    logging.exception(exception)
    response.write("Looks like you've found a page that doesn't exist...")
    response.set_status(404)

def handle_500(request, response, exception):
    logging.exception(exception)
    response.write('''Whoops we made a mistake somewhere!  Please report it to highlightpat@gmail.com with a screenshot or 
                    even just a one line description of what you were doing and we will be forever thankful!''')
    response.set_status(500)

#this is the information for all the handlers and their regexes and everything
app = webapp2.WSGIApplication([('/', otherhandlers.FrontPage),
                               ('/blog', otherhandlers.BlogRouterNaked),
                               ('/blog/(.*)', otherhandlers.BlogRouter),
                               ('/analytics', otherhandlers.AnalyticsHandler),
                               ('/script.js', otherhandlers.ScriptThang),
                               ('/robots.txt', otherhandlers.Robots),
                               ('/newest', otherhandlers.NewestVideoHandler),
                               ('/top', otherhandlers.TopVideoHandler),
                               ('/termsofservice', otherhandlers.TermsOfService),
                               ('/contact', otherhandlers.Contact),
                               ('/hashtag/(.*)', otherhandlers.HashtagHandler),
                               ('/search', otherhandlers.SearchHandler),
                               ('/advancedsearch', otherhandlers.AdvancedSearchHandler),
                               ('/ajaxtest', otherhandlers.AjaxTest),
                               ('/tester', otherhandlers.Tester),
                               ('/about', otherhandlers.About),
                               ('/working', otherhandlers.Working),
                               ('/noaccess', otherhandlers.NoAccess),
                               ('/videohandler', videohandlers.VideoHandler),
                               ('/uploadingvideo/(.*)', videohandlers.UploadHandler),
                               ('/videoinfo/(.*)', videohandlers.VideoInfoHandler), 
                               ('/serve/([^/]+)?', videohandlers.ServeHandler),
                               ('/encodevideo/(.*)', videohandlers.EncodeVideoHandler),
                               ('/videonotification', videohandlers.VideoNotification),
                               ('/video/(.*)', videohandlers.VideoPermalink),
                               ('/deletevideo', videohandlers.DeleteVideoPermalink),
                               ('/profile', profilehandlers.Profile),
                               ('/editprofile', profilehandlers.EditProfile),
                               ('/user/(.*)', profilehandlers.UserProfileRedirect),
                               (r'/profileupload/(.*)', profilehandlers.ProfileUploadHandler),
                               webapp2.Route(r'/profile<:/?><profile_id:[0-9]*?>', defaults={"profile_id":""}, handler=profilehandlers.ProfilePage, name="profile"),
                               ('/login', basehandler.Login),
                               #SimpleAuth stuff is here down
                               webapp2.Route('/auth/<provider>', handler='pagehandlers.basehandler.AuthHandler:_simple_auth', name='auth_login'),
                               webapp2.Route('/auth/<provider>/callback', handler='pagehandlers.basehandler.AuthHandler:_auth_callback', name='auth_callback'),
                               webapp2.Route('/logout', handler='pagehandlers.basehandler.AuthHandler:logout', name='logout')],
                               debug=True, 
                               config=config) #Needed for SimpleAuth

app.error_handlers[404] = handle_404
app.error_handlers[500] = handle_500