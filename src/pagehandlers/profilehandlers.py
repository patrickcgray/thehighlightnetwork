#this file has everything relating to the user's personal profile

#external imports
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
from google.appengine.ext import blobstore

from geopy import geocoders

import logging
import re

#internal imports
from basehandler import BlogHandler
from models.dbmodels import User
from models.dbmodels import UniqueUsername
from models.dbmodels import Video

class Profile(BlogHandler):
    def get(self):
        if self.get_user():
            user = self.get_user()
            profile_id = user['model_id']
            
            #this means they have completed their profile at least once and gave a username
            #so they can go see their actual page
            if user['username']:
                self.redirect('/profile/%s' % (profile_id))
            else:      
                self.redirect('/editprofile')
        else:
            self.redirect("/login")
 
#this lets me do /user/username and it redirects to their actual profile           
class UserProfileRedirect(BlogHandler):
    def get(self, username):
        user = self.get_user()
        if user:
            searched_user_list = User.query(User.username == username).fetch(1)
            if searched_user_list:
                searched_user = searched_user_list[0]
                self.redirect('/profile/' + str(searched_user.key.id()))
            else:
                self.render("frontpage.html", user=user, no_user=True, username=username)
            
        else:
            self.redirect("/login")
            
#this lets users provide a photo
class ProfileUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self, profile_id):
        upload_files = self.get_uploads('file')
        blob_info = upload_files[0]
        blobRef = blob_info.key()
        user = User.get_by_id(int(profile_id))
        user.avatar = blobRef
        user.put()
        user.created = None
        user.last_modified = None
        self.redirect('/profile/%s' % (profile_id))   

#this is the actual prof page
class ProfilePage(BlogHandler):
    def get(self, *args, **kwargs):
        user = self.get_user()
        if user:
            profile_id = int(kwargs.get("profile_id"))
            profileowner = User.get_by_id(profile_id)
            current_profile_id = user['model_id']
            
            videos = Video.query(Video.user_id == int(profile_id)).order(-Video.created).fetch(10)
            videos = list(videos)
            videos_to_display = []
            for video in videos:
                if video.title != "":
                    videos_to_display.append(video)
            
            quote = profileowner.quote            
            
            avatar=None
            if profileowner.avatar:
                try:
                    avatar = images.get_serving_url(profileowner.avatar, size=None, crop=False, secure_url=None)
                except TransformationError:
                    logging.error('we just got a TransformationError while trying to open the users image')
                    avatar = None
            if not avatar:
                avatar = 'http://i.imgur.com/RE9OX.jpg'
            
            owner = False
            if current_profile_id == profile_id:
                owner = True               
                
            upload_url = blobstore.create_upload_url('/profileupload/%s' % (profile_id))
            
            self.render('profile.html', user=user, avatar=avatar, videos_to_display=videos_to_display,
                        profile_id=profile_id, upload_url=upload_url, profileowner=profileowner, owner=owner)
        else:
            self.render('login.html')

#user is sent here the first time they try to view their profile and when they want to edit it
class EditProfile(BlogHandler):
    def get(self):
        if not self.get_user():
            self.redirect("/login")
        else:
            user = self.get_user()
                
            user_db_qry = User.query(User.oauth2_id == user['oauth2_id'])
            user_db_list = user_db_qry.fetch(1)
            currentregistereduser = user_db_list[0]
            has_username = False
            
            name = ""
            if currentregistereduser.name:
                name = currentregistereduser.name
            username = ""
            if currentregistereduser.username:
                username = currentregistereduser.username
                has_username = True
            bio = ""
            if currentregistereduser.bio:
                bio = currentregistereduser.bio
            quote = ""
            if  currentregistereduser.quote:
                 quote = currentregistereduser.quote
            email = ""
            if currentregistereduser.email:
                email = currentregistereduser.email
            geo_center = ""
            if currentregistereduser.geo_center:
                geo_center = currentregistereduser.geo_center
            high_school = ""
            if currentregistereduser.high_school:
                high_school = currentregistereduser.high_school
            university = ""
            if currentregistereduser.university:
                university = currentregistereduser.university
            sports_played = ""
            if currentregistereduser.sports_played:
                sports_played = currentregistereduser.sports_played
                
            self.render('editprofile.html', bio=bio, name=name, username=username, quote=quote, GPS=geo_center, user = user, 
                        email=email, has_username=has_username, high_school=high_school, university=university, sports_played=sports_played)
            
    def post(self):
        name = self.request.get('name')
        username = self.request.get('username')
        bio = self.request.get('bio')
        quote = self.request.get('quote')
        geo_center = self.request.get('geo_center')
        email = self.request.get('email')
        sports_played = self.request.get_all('sports_played')
        high_school = self.request.get('high_school')
        university = self.request.get('university')
                
        user = self.get_user()
        
        username_is_valid = re.match('^[\w-]+$', username) is not None
        
        if not username_is_valid and not user['username']:
            error = "Sorry, the username can only be letters and numbers."
            self.render("editprofile.html", name=name, username=username, bio=bio, quote=quote, email=email, error=error, user=user, 
                        geo_center=geo_center, high_school=high_school, university=university, sports_played=sports_played) 
        
        elif username or user['username']:
            if not username:
                username = user['username']
            keyname =  "username-" + str(username)
            previous_username = UniqueUsername.get_by_id(keyname)
            if previous_username != None and previous_username.user_id_record != str(user['model_id']):
                error = "Sorry, that username is already in use."
                self.render("editprofile.html", name=name, username=username, bio=bio, quote=quote, email=email, error=error,
                             user=user, geo_center=geo_center, high_school=high_school, university=university, sports_played=sports_played)
            else:
                username_record = UniqueUsername.get_or_insert(keyname, user_id_record=str(user['model_id']))
            
                user_db_qry = User.query(User.oauth2_id == user['oauth2_id'])
                user_db_list = user_db_qry.fetch(1)
                currentregistereduser = user_db_list[0]
                
                profile_id = currentregistereduser.key.id()
                currentregistereduser.name = name
                currentregistereduser.username = username
                currentregistereduser.bio = bio
                currentregistereduser.quote = quote
                currentregistereduser.email = email
                currentregistereduser.high_school = high_school
                currentregistereduser.university = university
                if sports_played:
                    currentregistereduser.sports_played = sports_played
                
                error = None
                GPSlocation = None
                if geo_center:
                    g = geocoders.GoogleV3()
                    #to catch an error where there is no corresponding location
                    try:
                        #to catch an error where there are multiple returned locations
                        try:
                            place, (lat, lng) = g.geocode(geo_center)
                            place, searched_location = g.geocode(geo_center)
                        except ValueError:
                            geocodespot = g.geocode(geo_center, exactly_one=False)
                            place, (lat, lng) = geocodespot[0]
                            place, searched_location = geocodespot[0]
                        GPSlocation = "("+str(lat)+", "+str(lng)+")"                 
    
                    #this is straight from the docs:  http://code.google.com/p/geopy/wiki/Exceptions and happens when there is no location that matches
                    except geocoders.googlev3.GQueryError:
                        logging.error('could not find the spot')
                        error = "We cannot find " + geo_center +"... try to be a little more specific or search a nearby location."
                            
                    except geocoders.googlev3.GTooManyQueriesError:
                        logging.error('the request did not go through because there are too many queries')
                        #TODO
                        something = 'nada'
                        
                if error:
                    self.render('editprofile.html', bio=bio, name=name, username=username, email=email, error=error, quote=quote, 
                                user = user, geo_center=geo_center, high_school=high_school, university=university, sports_played=sports_played)
                
                else:            
                    if GPSlocation:
                        currentregistereduser.geo_center = GPSlocation
                    if not currentregistereduser.geo_center:
                        currentregistereduser.geo_center = None
                    
                    currentregistereduser.put()
                    currentregistereduser.created = None
                    currentregistereduser.last_modified = None
                    currentregistereduser.avatar = None
                    self.session['_current_user'] = currentregistereduser.to_dict()
                    
                    self.redirect('/profile/%s' % (profile_id))
                    
        elif not username:
                    
            error = "Come on you can put a little something.  At least a username is required."
            self.render("editprofile.html", name=name, username=username, bio=bio, quote=quote, email=email, error=error, user=user, 
                        geo_center=geo_center, high_school=high_school, university=university, sports_played=sports_played)   
