import webapp2
import json
import jinja2
import os
import logging

from simpleauth import SimpleAuthHandler
import secrets
#added to include needed modules for SimpleAuth

from models.dbmodels import User

#added to include needed modules for SimpleAuth
from webapp2_extras import sessions, auth
from google.appengine.api import urlfetch

urlfetch.set_default_fetch_deadline(60) 

#initalize the jinja2 template
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader('templates'),
							   autoescape = True)
#I need this Jinja2 filter to be able to pass variables into the templaes and use them in Javascript
jinja_env.filters['json_encode'] = json.dumps

#this is my base handler and gives some basic functions that most of my handlers use
class BlogHandler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		return render_str(template, **params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))
	#this doesn't quite work for the general case right now
	def error(self, code):
		super(BlogHandler, self).error(code)
		if code == 404:
			self.render("working.html")
		if code == 500:
			self.render("servererror.html")
	
	# Output 404 page

	def dispatch(self):
		# Get a session store for this request.
		self.session_store = sessions.get_store(request=self.request)

		try:
			# Dispatch the request.
			webapp2.RequestHandler.dispatch(self)
		finally:
			# Save all sessions.
			self.session_store.save_sessions(self.response)

	@webapp2.cached_property
	def session(self):
		# Returns a session using the default cookie key.
		return self.session_store.get_session() 
		
	@webapp2.cached_property
	def logged_in(self):
		"""Returns true if a user is currently logged in, false otherwise"""
		try:
			return self.session['_user_id'] is not None
		except KeyError:
			return False
	
	def get_user(self):
		if self.logged_in:
			return self.session['_current_user']
		else:
			return False
 
class Login(BlogHandler):
	def get(self):
		user = self.get_user()
		self.render('login.html', user = user, logged_in = self.logged_in)

	def post(self):
		password = self.request.get('password')
		user = self.get_user()
		
		if password == 'highlightitup':
			self.render('login.html', user = user, logged_in = self.logged_in)
		else: 
			error = 'Sorry, wrong password...'
			self.render('logincheck.html', user=user, error=error)
        
#SimpleAuth authentication handler
class AuthHandler(BlogHandler, SimpleAuthHandler):
    """Authentication handler for all kinds of auth."""
    def _on_signin(self, data, auth_info, provider):
        """Callback whenever a new or existing user is logging in.
        data is a user info dictionary.
        auth_info contains access token or oauth token and secret.

        See what's in it with logging.info(data, auth_info)
        """
            
        auth_id = '%s:%s' % (provider, data['id'])
        
        # 1. check whether user exist, e.g.
        #    User.get_by_auth_id(auth_id)
        #
        # 2. create a new user if it doesn't
        #    User(**data).put()
        #
        # 3. sign in the user
        #    self.session['_user_id'] = auth_id
        #
        # 4. redirect somewhere, e.g. self.redirect('/profile')
        #
        # See more on how to work the above steps here:
        # http://webapp-improved.appspot.com/api/webapp2_extras/auth.html
        # http://code.google.com/p/webapp-improved/issues/detail?id=20
    
        currentregistereduser = None
        #check for user existance upon login/registration
        try:
            user_db_qry = User.query(User.oauth2_id == auth_id)
            user_db_list = user_db_qry.fetch(1)
            currentregistereduser = user_db_list[0]
            
        #if the user does not exist yet
        except IndexError:
            name = None
            #
            try:
                name = data['name']
            except KeyError:
                name = None
                
            user_db = User(
                name=name,
                oauth2_id=auth_id,
                prestige = 100,
                )
            user_db.put()
            user_db.model_id = user_db.key.id()
            user_db.put()
            
            currentregistereduser = user_db
                        
        self.session['_user_id'] = auth_id
        self.session['data'] = data
        currentregistereduser.created = None
        currentregistereduser.last_modified = None
        currentregistereduser.avatar = None
        self.session['_current_user'] = currentregistereduser.to_dict()
        
        if currentregistereduser.username:
            self.redirect("/")
        else:
            self.redirect("/profile")
    
    def logout(self):
        self.session['_user_id'] = None
        self.session['data'] = None
        self.session['_current_user'] = None
        self.redirect('/login')
    
    def _callback_uri_for(self, provider):
        return self.uri_for('auth_callback', provider=provider, _full=True)
    
    def _get_consumer_info_for(self, provider):
        """Should return a tuple (key, secret) for auth init requests.
        For OAuth 2.0 you should also return a scope, e.g.
        ('my app id', 'my app secret', 'email,user_about_me')
        
        The scope depends solely on the provider.
        See example/secrets.py.template
        """
        return secrets.AUTH_CONFIG[provider]        

def render_str(template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)