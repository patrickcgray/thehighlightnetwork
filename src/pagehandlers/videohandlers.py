#this file has all of the small handlers that do not need their own file

#external imports
import webapp2
import json
import urllib
import urllib2
import logging
from operator import attrgetter
import time

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import files

from zencoder import Zencoder
from geopy import geocoders

#internal imports
from basehandler import BlogHandler
from models.dbmodels import User
from models.dbmodels import Video
from models.dbmodels import VideoComment
from models.dbmodels import Vote


            
class VideoHandler(BlogHandler):
    def get(self):      
        user = self.get_user()        
        if user:
            user_id = user['model_id']
            upload_url = blobstore.create_upload_url('/uploadingvideo/' + str(user_id))
            self.render('videohandler.html', user=user, upload_url=upload_url)
        else:
            self.redirect('/login')
        
class VideoPermalink(BlogHandler):
    def get(self, video_id):      
        user = self.get_user()
        video = Video.get_by_id(int(video_id)) 
        
        owner = False
        if user:
            if video.user_id == user['model_id']:
                owner = True
        
        comments = VideoComment.query(VideoComment.video_id == int(video_id)).order(VideoComment.created).fetch(50)
        
        potential_related_videos = Video.query(Video.subcategory == video.subcategory).order(Video.created).fetch(5)
        
        if video in potential_related_videos:
            potential_related_videos.remove(video)
            
        related_videos = []
        for potential_video in potential_related_videos:
            if potential_video.mp4_video_ref and potential_video.webm_video_ref and potential_video.title != "":
                related_videos.append(potential_video)
        self.render('videopermalink.html', user=user, video=video, comments=comments, related_videos=related_videos, owner=owner)
        
    def post(self, video_id):
        content = self.request.get('content')
        vote = self.request.get('vote')
        user = self.get_user() 
        user_id = user['model_id']
        
        if content:            
            c = VideoComment(content = content, 
                             video_id=int(video_id),
                             upvotes = 0,
                             submitter = user['username'],
                             user_id = user_id,
                             downvotes = 0)
            c.put()
            video = Video.get_by_id(int(video_id))
            video.comment_count = video.comment_count + 1
            video.put()
            
            currentregistereduser = User.get_by_id(int(user['model_id']))
            currentregistereduser.prestige = currentregistereduser.prestige + 2
            currentregistereduser.put()
            #video_comment_cache(int(group_id), True)
            self.redirect('/video/%s' % video_id)
        elif vote:
            keyname = str(user_id) + "-" + str(video_id) + "-post"
            previous_vote = Vote.get_by_id(keyname)
            #previous_vote = Vote.get_by_key_name(keyname)
            if previous_vote != None:
                video = Video.get_by_id(int(video_id))
                vote_count = video.upvotes - video.downvotes
                self.response.write(vote_count)
            else:
                vote_record = Vote.get_or_insert(keyname, vote_record=str(user_id))
                video = Video.get_by_id(int(video_id))
                vote_count = video.upvotes - video.downvotes
                if vote == "upvote":
                    vote_count = vote_count + 1
                    video.upvotes = video.upvotes + 1
                    video.put()
                    currentregistereduser = User.get_by_id(int(video.user_id))
                    currentregistereduser.prestige = currentregistereduser.prestige + 1
                    currentregistereduser.put()
                elif vote == "downvote":
                    vote_count = vote_count - 1
                    video.downvotes = video.downvotes + 1
                    video.put()
                self.response.write(vote_count)
        else:
            something = 'nada'
            
class DeleteVideoPermalink(BlogHandler):
    def post(self):
        video_id = self.request.get('video_id')
        user = self.get_user()  
        
        video = Video.get_by_id(int(video_id))
        
        #TODO this isn't really secure
        if user:
            if video.user_id == user['model_id']:
                key = video.put()
                blobstore.delete(video.original_video_ref)
                blobstore.delete(video.webm_video_ref)
                blobstore.delete(video.mp4_video_ref)
                key.delete()
                
                image = None
                current_time = int(time.time())
                if current_time % 4 == 0:
                    image = "http://i.imgur.com/5ayyxI7.jpg"
                elif current_time % 3 == 0:
                    image = "http://i.imgur.com/FsNsx6G.jpg"
                elif current_time % 2 == 0:
                    image = "http://i.imgur.com/apDsYlz.jpg"
                else:
                    image = "http://i.imgur.com/2md8HRk.jpg"  
                
                self.render('deletesuccess.html', image=image, user=user)
        else:
            self.rediret("noaccess.html")

            

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
  def post(self, user_id):
    upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
    blob_info = upload_files[0]
    user = User.get_by_id(int(user_id))
    
    video = Video(
        title = "",
        geo_center = "",
        sportcategory = "",
        subcategory = "",
        upvotes = 0,
        downvotes = 0,
        submitter = user.username,
        comment_count = 0,
        user_id = int(user_id),
        original_video_ref = blob_info.key(),
        mp4_video_ref = None,
        webm_video_ref = None,
        tags = [],
        spam = 0,
        spamComfirmed = False)
    video.put()
    
    #should I do this with some sort of response in a post request and send some sort of token so that it can't be done randomly
    self.redirect('/encodevideo/%s' % video.key.id())
        
class EncodeVideoHandler(BlogHandler):
    def get(self, video_id):
        video = Video.get_by_id(int(video_id)) 
        #Zencoder with API Key
        client = Zencoder('9b3c90c93b718a83dba3e343e7ec014a')
        # configure outputs with dictionaries
        mp4 = {
                     'label': ['mp4', video_id],
                     'format': 'mp4'
                 }
        webm = {
                  'label': ['webm', video_id],
                  'format': 'webm'
              }
        notifications = "http://thehighlightnetwork.appspot.com/videonotification"
        
        # the outputs kwarg requires an iterable
        outputs = (mp4, webm)
        response_from_job = client.job.create('http://thehighlightnetwork.appspot.com/serve/'+ str(video.original_video_ref), 
                                              outputs=outputs, 
                                              notifications=notifications)
        
        #need to use this to test if the response is good
        logging.info(response_from_job.code)           #hopefully 201
        #response_id = int(response_from_job.body['id'])
        
        response_body = response_from_job.body
        
        logging.info(response_body)
        logging.info(video_id)  
        
        self.redirect('/videoinfo/%s' % video_id)
        
class VideoInfoHandler(BlogHandler):
    def get(self, video_id):      
        user = self.get_user()
        
        video = Video.get_by_id(int(video_id))
        if user:
            if video.user_id == user['model_id']:
                self.render('videoinfo.html', user=user)
            else:
                self.redirect('/noaccess')
        else:
            self.redirect('/noaccess')
            
    def post(self, video_id):
        title = self.request.get('title')
        sportcategory = self.request.get('sportcategory')
        sportlevel = self.request.get('sportlevel')
        
        tags = self.request.get('tags')
        shoutouts = self.request.get('shoutouts')
        subcategory = self.request.get('subcategory')
        description = self.request.get('description')
        winner = self.request.get('winner')
        loser = self.request.get('loser')
        geo_center = self.request.get('geo_center')
        
        user = self.get_user()
        
        if title and sportcategory != "choose" and sportlevel != "choose":
        
            video = Video.get_by_id(int(video_id))
            
            video.title = title
            video.sportcategory = sportcategory
            video.sportlevel = sportlevel
            
            if tags:
                try:
                    tags = tags.split(',')
                    for i in xrange(len(tags)):
                        if tags[i][0] == ' ':
                            tags[i] = tags[i][1:]
                        if tags[i][0] == '#':
                            tags[i] = tags[i][1:]
                except IndexError:
                    dud_value = None
            if shoutouts:
                shoutouts = shoutouts.split(', ')
                for i in xrange(len(shoutouts)):
                    if shoutouts[i][0] == '@':
                        shoutouts[i] = shoutouts[i][1:]
                video.shoutouts = shoutouts                    
            if subcategory != "choose":
                video.subcategory = subcategory
            if description:
                video.description = description
            if winner:
                video.winner = winner
            if loser:
                video.loser = loser
                
                
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
                    logging.error('we hit an error here in that we could not find it')
                    error = "We cannot find '" + geo_center +"' try to be a little more specific or search a nearby location."
                except geocoders.googlev3.GTooManyQueriesError:
                    logging.error('the request did not go through because there are too many queries')
                    #TODO
                    something = 'nada'
                    
            if error:
                self.render('videoinfo.html', user=user, error=error, title=title, sportcategory=sportcategory, sportlevel=sportlevel,
                tags=tags, subcategory=subcategory, description=description, winner=winner, loser=loser, geo_center=geo_center)
                
            else:
                if GPSlocation:
                    video.geo_center = GPSlocation
                if not video.geo_center:
                    video.geo_center = None
                
                video.put()
                
                currentregistereduser = User.get_by_id(int(user['model_id']))
                currentregistereduser.prestige = currentregistereduser.prestige + 10
                currentregistereduser.put()
                
                
                #get this to redirect to a permalink
                self.redirect('/video/%s' % video_id)
            
        else:
            error = "Please complete all the required sections."
            self.render('videoinfo.html', user=user, error=error, title=title, sportcategory=sportcategory, sportlevel=sportlevel,
                        tags=tags, subcategory=subcategory, description=description, winner=winner, loser=loser, geo_center=geo_center)

     

class VideoNotification(BlogHandler):
    def post(self):
        json_string = self.request.body
        json_object = json.loads(json_string)
                               
        mp4_url = None
        webm_url = None
        
        #need the double if statements here in case they come in different order
        
        if json_object['outputs'][0]['label'][0] == 'mp4':
            mp4_url = json_object['outputs'][0]['url']
            
        if json_object['outputs'][1]['label'][0] == 'mp4':
            mp4_url = json_object['outputs'][1]['url']
        
        if json_object['outputs'][0]['label'][0] == 'webm':
            webm_url = json_object['outputs'][0]['url']
        
        if json_object['outputs'][1]['label'][0] == 'webm':
            webm_url = json_object['outputs'][1]['url']
        
        video_id = json_object['outputs'][0]['label'][1]
        
        logging.info('mp4_url:  ' + mp4_url)
        logging.info('webm_url:  ' + webm_url)
        
        try:
            encoded_video_receiver(mp4_url, webm_url, video_id)
        except Exception, e:
            logging.error('Error was:' + e)
            time.sleep(5)
            try:
                encoded_video_receiver(mp4_url, webm_url, video_id)
            except:
                logging.error('the second try did not work either')
                 

            
def encoded_video_receiver(mp4_url, webm_url, video_id):
    logging.info('starting the encoded_video_receiver')
    if mp4_url and webm_url:
        video = Video.get_by_id(int(video_id))
        try:
            #adding the mp4 video ref
            mp4_file_name = files.blobstore.create(mime_type='video/mp4')          
            mp4_video = urllib2.urlopen(mp4_url)
            with files.open(mp4_file_name, 'a') as mp4_f:
                mp4_f.write(mp4_video.read())
            files.finalize(mp4_file_name)   
            mp4_blob_key = files.blobstore.get_blob_key(mp4_file_name) 
            video.mp4_video_ref = mp4_blob_key
            
            #adding the webm video ref
            webm_file_name = files.blobstore.create(mime_type='video/webm')
            webm_video = urllib2.urlopen(webm_url)
            with files.open(webm_file_name, 'a') as webm_f:
                webm_f.write(webm_video.read())
            files.finalize(webm_file_name)   
            webm_blob_key = files.blobstore.get_blob_key(webm_file_name) 
            video.webm_video_ref = webm_blob_key
            
            video.put()
            
            logging.info('just saved the video in the datastore')
            
        except urllib2.HTTPError, e:
            logging.error('HTTPError:  Failed somehow with a HTTPerror: ' + str(e))
            #time.sleep(10)
        except Exception, e:
            logging.error('Exception:  Failed somehow: ' + str(e))
    else:
        logging.error('need to resubmit the request and put it back on the queue')
                    
class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, blob_key):
        blob_key = str(urllib.unquote(blob_key))
        if not blobstore.get(blob_key):
            logging.error('we didnt get it on the first try')
            blob_key = str(urllib.unquote(blob_key))
            if not blobstore.get(blob_key):
                self.error(404)
                logging.error('we didnt get it on the second try either')
        else:
            self.send_blob(blobstore.BlobInfo.get(blob_key))
            