import webapp2
import json
import urllib
import urllib2
import logging
from operator import attrgetter
import time

from basehandler import BlogHandler
from models.dbmodels import User
from models.dbmodels import Video
from models.dbmodels import VideoComment
from models.dbmodels import Vote

class ScriptThang(BlogHandler):
    def get(self):
        self.render('script.js')

class FrontPage(BlogHandler):
    def get(self):
        sportcategory = self.request.get('sportcategory')
        subcategory = self.request.get('subcategory')
        sportlevel = self.request.get('sportlevel')
                
        user = self.get_user()
        
        if (sportcategory == '' or sportcategory == 'choose') and (subcategory == '' or subcategory == 'choose a subcategory') and (sportlevel == '' or sportlevel == 'choose'):
            the_query = Video.query().order(-Video.created)
            videos = the_query.fetch(20)
            videos_list = list(videos)
            videos_list = sorted(videos_list, key=attrgetter('score'), reverse=True)
            videos = []
            for video in videos_list:
                if video.mp4_video_ref and video.webm_video_ref and video.title != "":
                    videos.append(video)
            videos = videos[:12]
            
            self.render("frontpage.html", user=user, videos=videos)

                
        
        else:
            final_videos= []
            filters = []
            prelim_videos = []
            videos_list = []
            
            if subcategory != "choose a subcategory":
                the_query = Video.query(Video.subcategory == subcategory).order(-Video.created)
                videos = the_query.fetch(100)
                videos_list = list(videos)
                if sportlevel != "choose":
                    for video in videos_list:
                        if video.sportlevel == sportlevel:
                            prelim_videos.append(video)
                    videos_list = prelim_videos
            elif sportcategory != "choose":
                the_query = Video.query(Video.sportcategory == sportcategory).order(-Video.created)
                videos = the_query.fetch(100)
                videos_list = list(videos)
                if sportlevel != "choose":
                    for video in videos_list:
                        if video.sportlevel == sportlevel:
                            prelim_videos.append(video)
                    videos_list = prelim_videos
            elif sportlevel != "choose":
                the_query = Video.query(Video.sportlevel == sportlevel).order(-Video.created)
                videos = the_query.fetch(100)
                videos_list = list(videos)
                for video in videos_list:
                    if video.sportlevel == sportlevel:
                        prelim_videos.append(video)
                videos_list = prelim_videos
            else:
                filters = None
                the_query = Video.query().order(-Video.created)
                videos = the_query.fetch(100)
                videos_list = list(videos)
                
            if sportcategory != 'choose':
                filters.append(sportcategory)
            if subcategory != 'choose a subcategory':
                filters.append(subcategory)
            if sportlevel != 'choose':
                filters.append(sportlevel)

            #just to make sure they're ready to serve
            for video in videos_list:
                if video.mp4_video_ref and video.webm_video_ref and video.title != "":
                    final_videos.append(video)
            
            #TODO will need to so some sort of paging mechanism here
            self.render("frontpage.html", user=user, videos=final_videos, filters=filters)
  
        
class NewestVideoHandler(BlogHandler):
    def get(self):
        user = self.get_user()
        video_query = Video.query().order(-Video.created).fetch(50)
        video_list = list(video_query)
        videos = []
        for video in video_list:
            if video.mp4_video_ref and video.webm_video_ref and video.title != "":
                videos.append(video)
        videos = videos[:12]
        self.render("frontpage.html", user=user, videos=videos, newest=True) 
        
class AnalyticsHandler(BlogHandler):
    def get(self):
        user = self.get_user()
        if user['model_id'] == 5187942536445952:
            user_model = User.get_by_id(5187942536445952)
            user_model.admin = True
            user_model.put
            
            all_videos = Video.query()
            video_count = 0
            for v in all_videos:
                video_count = video_count + 1
            
            all_users = User.query()
            user_count = 0
            for u in all_users:
                user_count = user_count + 1
            
            all_comments = VideoComment.query()
            comment_count = 0
            for c in all_comments:
                comment_count = comment_count + 1
                
            all_votes = Vote.query()
            vote_count = 0
            for vs in all_votes:
                vote_count = vote_count + 1
                    
            self.response.write('There are ' + str(video_count) + ' videos.')
            self.response.write('<br>')
            self.response.write('There are ' + str(user_count) + ' users.')
            self.response.write('<br>')
            self.response.write('There are ' + str(comment_count) + ' comments.')
            self.response.write('<br>')
            self.response.write('There are ' + str(vote_count) + ' votes.')
        else:
            self.redirect('/noaccess')
        
class BlogRouter(BlogHandler):
    def get(self, rest):
        url = self.request.url        
        end_of_url = url.split('www.thehighlightnetwork.com/blog/')[1]
        self.redirect('http://blog.thehighlightnetwork.com/' + end_of_url)

class TopVideoHandler(BlogHandler):
    def get(self):
        user = self.get_user()
        video_query = Video.query().order(-Video.score).fetch(50)
        video_list = list(video_query)
        videos = []
        for video in video_list:
            if video.mp4_video_ref and video.webm_video_ref and video.title != "":
                videos.append(video)
        videos = videos[:12]
        self.render("frontpage.html", user=user, videos=videos, top=True) 
        
class SearchHandler(BlogHandler):
    def get(self):
        search_tag = self.request.get('search_tag') 
        
        if search_tag[0] == '#':
            self.redirect('/hashtag/' + search_tag[1:])
        elif search_tag[0] == '@':
            self.redirect('/user/' + search_tag[1:])
        else:
            self.redirect('/hashtag/' + search_tag)
            
class AdvancedSearchHandler(BlogHandler):
    def get(self):
        user = self.get_user() 
        self.render("advancedsearch.html", user=user)
    
    def post(self):
        search_user = self.request.get('search_user')
        search_tag = self.request.get('search_tag')
        search_shoutout = self.request.get('search_shoutout')
        
        if search_tag:
            if search_tag[0] == '#':
                self.redirect('/hashtag/' + search_tag[1:])
            else:
                self.redirect('/hashtag/' + search_tag)
                
        elif search_user:
            if search_user[0] == '@':
                self.redirect('/user/' + search_user[1:])
            else:
                self.redirect('/user/' + search_user)
        
        elif search_shoutout:
            if search_shoutout[0] == '@':
                self.redirect('/user/' + search_shoutout[1:])
            else:
                self.redirect('/user/' + search_shoutout)
            
class HashtagHandler(BlogHandler):
    def get(self, search_tag):
        user = self.get_user()
        the_query = Video.query(Video.tags.IN([search_tag])).order(-Video.created)
        videos = the_query.fetch(100)
        videos_list = list(videos)
        
        #just to make sure they're ready to serve
        final_videos = []
        for video in videos_list:
            if video.mp4_video_ref and video.webm_video_ref and video.title != "":
                final_videos.append(video)
            
        self.render("frontpage.html", user=user, videos=final_videos, tag=search_tag)
  
class TermsOfService(BlogHandler):   
    def get(self):
        user = self.get_user()
        self.render('termsofservice.html', user = user)
        
class Contact(BlogHandler):
    def get(self):
        user = self.get_user()
        self.render('contact.html', user = user)

class About(BlogHandler):
    def get(self):
        user = self.get_user()
        self.render('about.html', user = user)

class AjaxTest(BlogHandler):
    def get(self):
        user = self.get_user()       
        self.render('ajaxtest.html', user = user)
    def post(self):
        user = self.get_user()
        word = self.request.get('w')
        logging.info(word)
        #print "Content-Type: text/html\n"
        self.response.write('<p>The secret word is ' + word + '<p>')

class Robots(BlogHandler):
    def get(self):
        self.render('robots.txt')

#sent whenever a page has not been completed
class Working(BlogHandler):
    def get(self):
        user = self.get_user()
        self.render('working.html', user = user)
        
class NoAccess(BlogHandler):
    def get(self):
        user = self.get_user()
        self.render('noaccess.html', user = user)
        
class Tester(BlogHandler):
    def get(self):
        logout = users.create_logout_url(self.request.uri) 
        user = users.get_current_user()
        self.render("working.html", user=user, logout=logout)