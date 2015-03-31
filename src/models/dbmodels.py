#this document has all of my database models

from google.appengine.ext import db
from google.appengine.ext import ndb
import jinja2
import os
import json

#need to import this from basehandler or the blog.py but isn't working for some reason
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader('templates'),
                               autoescape = True)
#I need this Jinja2 filter to be able to pass variables into the templaes and use them in Javascript
jinja_env.filters['json_encode'] = json.dumps

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class Video(ndb.Model):
    title = ndb.StringProperty(required = True)
    description = ndb.TextProperty()
    geo_center = ndb.StringProperty()
    location = ndb.StringProperty()
    sportcategory = ndb.StringProperty(required = True)
    subcategory = ndb.StringProperty()
    tags = ndb.StringProperty(repeated = True)
    shoutouts = ndb.StringProperty(repeated = True)
    sportlevel = ndb.StringProperty()
    source = ndb.StringProperty()
    winner = ndb.StringProperty()
    loser = ndb.StringProperty()
    
    original_video_ref = ndb.BlobKeyProperty()
    webm_video_ref = ndb.BlobKeyProperty()
    mp4_video_ref = ndb.BlobKeyProperty()
    
    upvotes = ndb.IntegerProperty(required = True)
    downvotes = ndb.IntegerProperty(required = True)
    comment_count = ndb.IntegerProperty()
    score = ndb.ComputedProperty(lambda self: self.upvotes - self.downvotes)
    
    created = ndb.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    submitter = ndb.StringProperty(required = True)
    user_id = ndb.IntegerProperty()

    spam = ndb.IntegerProperty()
    spamComfirmed = ndb.BooleanProperty()
    
    def video_front(self):
        return render_str("video_front.html", v = self)
    
    def video_main(self):
        #self._render_text = self.description.replace('\n', '<br>')
        return render_str("video_main.html", v = self)
    
class VideoComment(ndb.Model):
    content = ndb.TextProperty(required = True)
    created = ndb.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    submitter = ndb.StringProperty()
    user_id = ndb.IntegerProperty()
    video_id = ndb.IntegerProperty(required = True)
    
    upvotes = ndb.IntegerProperty(required = True)
    downvotes = ndb.IntegerProperty(required = True)
    
    def render(self):
        #self._render_text = self.content.replace('\n', '<br>')
        return render_str("videocomment.html", c = self)

class User(ndb.Model):
    name = ndb.StringProperty()
    username = ndb.StringProperty()
    oauth2_id = ndb.StringProperty()
    model_id = ndb.IntegerProperty()
    email = ndb.StringProperty()
    bio = ndb.StringProperty()
    prestige = ndb.IntegerProperty()
    quote = ndb.StringProperty()
    avatar = ndb.BlobKeyProperty()
    geo_center = ndb.StringProperty()
    sports_played = ndb.StringProperty(repeated=True)
    high_school = ndb.StringProperty()
    university = ndb.StringProperty()
    awards = ndb.StringProperty()
    featured_videos = ndb.StringProperty()

    spam = ndb.IntegerProperty()
    spamComfirmed = ndb.BooleanProperty()
    created = ndb.DateTimeProperty(auto_now_add = True)
    last_modified = ndb.DateTimeProperty(auto_now = True)
    admin = ndb.BooleanProperty()

#this is the mechanism for preventing duplicate voting
class Vote(ndb.Model):
    vote_record = ndb.StringProperty() # just simply seeing if this user has voted before
    
class UniqueUsername(ndb.Model):
    user_id_record = ndb.StringProperty() # just simply seeing if this user has voted before