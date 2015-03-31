#this document has all of my memcache
from google.appengine.api import memcache
from google.appengine.ext import ndb
import logging
from operator import attrgetter

from dbmodels import User
from dbmodels import Video
from dbmodels import VideoComment

def individual_video_cache(video_id, update = False):
    key=str(video_id)+"_individual_video"
    video = memcache.get(key)
    if video is None or update:
        video = Video.get_by_id(int(video_id))
        video = list(video)
        memcache.set(key, video)
    return video

def profile_video_cache(user_id, update = False):
    key=str(user_id)+"_personalvideos"
    videos = memcache.get(key)
    if videos is None or update:
        videos = Video.query(Video.user_id == int(user_id)).order(-Video.created)
        videos = list(videos)
        memcache.set(key, videos)
    return videos

#this is not correct and needs to be fixed to do the main page
def frontpage_video_cache(update = False):
    key="frontpage_videos"
    videos = memcache.get(key)
    if videos is None or update:
        videos =  Video.query().order(-Video.created).fetch(200)
        videos = sorted(videos, key=attrgetter('score'), reverse=True)
        videos = list(videos)
        videos = videos[:10]
        memcache.set(key, videos)
    return videos

def recent_video_cache(update = False):
    key="most_recent_videos"
    videos = memcache.get(key)
    if videos is None or update:
        videos =  Video.query().order(-Video.created).fetch(10)
        videos = list(videos)
        memcache.set(key, videos)
    return videos

def user_cache(update = False):
    key = 'users'
    users = memcache.get(key)
    if users is None or update:
        users = User.query().order(-User.created, User.name).fetch(10)
        users = list(users)
        memcache.set(key, users)
    return users

def video_comment_cache(video_id, update = False):
        key = str("video_comments_" + video_id)
        comments = memcache.get(key)
        if comments is None or update:
                comments = VideoComment.query(VideoComment.video_id == int(video_id)).order(VideoComment.created).fetch(50)
                comments = list(comments)
                memcache.set(key, comments)
        return comments