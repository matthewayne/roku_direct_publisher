
import json
import os
from flask import Flask, request, redirect, url_for, render_template, flash
import datetime
import hashlib
from video_metadata import get_metadata


SERVER_NAME = "http://localhost:8080/"
UPLOAD_FOLDER = '/feed/temp'
ALLOWED_EXTENSIONS = set(['m4v', 'mp4', 'mov'])
SECRET_KEY = "dvk9vkr0egao4n25lfc8"
APP_ROOT = os.path.dirname(os.path.abspath(__file__)) 
APP_FEED = os.path.join(APP_ROOT, 'feed')
APP_VIDEO = os.path.join(APP_FEED, 'videos')
APP_THUMBNAIL = os.path.join(APP_FEED, 'thumbnails')

app = Flask(__name__, static_url_path='/feed', static_folder='feed')

app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def landing():
  feed = get_feed()
  try:
    videos = feed['shortFormVideos']
  except KeyError:
    videos = None
  return render_template("home.html", videos=videos)

@app.route('/edit/channel', methods=['GET', 'POST'])
def edit_channel():
    feed = get_feed()
    if request.method == 'POST':
      if len(request.form["channel_lang"]) == 0 or len(request.form["channel_name"]) == 0:
        flash('please fill out the name and language')
        return redirect(request.url)
      else:
        feed['providerName'] = str(request.form['channel_name'])
        feed['language'] = str(request.form['channel_lang'])
        print feed
        set_feed(feed)
        return "changes saved<br><a href=\"\\\">Go home</a>"

    elif request.method == 'GET':
      try:
        channel_name = feed['providerName']
        channel_lang = feed['language']
      except KeyError:
        channel_name, channel_lang = None, None
      return render_template(
        "edit_channel.html",
        channel_lang = channel_lang,
        channel_name = channel_name )

@app.route('/edit/shortFormVideos/', methods=['GET', 'POST'])
@app.route('/edit/shortFormVideos/<vid_id>', methods=['GET', 'POST'])
def upload_file(vid_id=None):
  feed = get_feed()
  if request.method == 'POST':
      
      if "video_title" not in request.form.keys():
        flash('No video title entered')
        return redirect(request.url)
      if "video_description" not in request.form.keys():
        flash('No video description entered')
        return redirect(request.url)

      if 'video_thumbnail' not in request.files:
          flash('No video thumbnail uploaded')
          return redirect(request.url)
      video_thumbnail = request.files['video_thumbnail']
      if video_thumbnail.filename == '':
          flash('No thumbnail file')
          return redirect(request.url)

      if 'video' not in request.files:
          flash('No video uploaded')
          return redirect(request.url)
      video = request.files['video']
      if video.filename == '':
          flash('No thumbnail file')
          return redirect(request.url)

      video_url, quality, vid_type, duration = process_video(video)
      thumbnail_url = process_thumbnail(video_thumbnail)
      
      if not vid_id:
        try:
          largest_id = max([vid["id"] for vid in feed['shortFormVideos']])
          vid_id = largest_id + 1
        except KeyError:
          vid_id = 1
          feed["shortFormVideos"] = []
      
        dateAdded = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "+00:00"

        feed["shortFormVideos"].append({
          "id":vid_id,
          "title": request.form['video_title'],
          "content":{
            "dateAdded": dateAdded,
            "videos": [
              {
              "url": video_url,
              "quality": quality,
              "videoType":vid_type
              }],
              "duration": duration
            },
            "thumbnail": thumbnail_url,
            "shortDescription":request.form['video_description']
          })
      else:
        target_index = next(index for (index, d) in enumerate(feed["shortFormVideos"]) if d["id"] == vid_id)
        feed["shortFormVideos"][target_index] = {
          "id":vid_id,
          "title": request.form['video_title'],
          "content":{
            "dateAdded": dateAdded,
            "videos": [
              {
              "url": video_url,
              "quality": quality,
              "videoType":vid_type
              }],
              "duration": duration
            },
            "thumbnail": thumbnail_url,
            "shortDescription":request.form['video_description']
          }
      set_feed(feed)
      return "video added to feed<br><a href=\"\\\">Go home</a>"
  elif request.method == 'GET':
    if vid_id:
      try:
        video_title = feed['providerName']
        video_description = feed['language']
      except KeyError:
        video_title, video_description = None, None
      return render_template(
        "edit_shortFormVideos.html",
        video_title = video_title,
        video_description = video_description )
    else:
      video_title, video_description = None, None
      return render_template(
        "edit_shortFormVideos.html",
        video_title = video_title,
        video_description = video_description )

def process_video(video):
  vid_type = str(video.filename[-3:]).upper()

  video_blob = video.read()
  video_key = hashlib.md5(video_blob).hexdigest()
  file_path = os.path.join(APP_VIDEO, video_key + ".%s" % vid_type)
  f =open(file_path, 'w')
  f.write(video_blob)
  f.close()
  video_url = SERVER_NAME + 'feed/videos/%s.%s' % (video_key, vid_type)
  
  ( quality, duration ) = get_metadata(file_path)

  print ( video_url, quality, vid_type, duration )

  return ( video_url, quality, vid_type, duration )


def process_thumbnail(thumbnail):
  video_blob = thumbnail.read()
  thumb_key = hashlib.md5(video_blob).hexdigest()
  file_path = os.path.join(APP_THUMBNAIL, thumb_key)
  f =open(file_path, 'w')
  f.write(video_blob)
  f.close()
  thumbnail_url = SERVER_NAME + 'feed/thumbnails/%s' % thumb_key

  return thumbnail_url
   

def get_feed():
  try:
    f = open(os.path.join(APP_FEED, 'feed.json'), 'r')
    feed = json.loads(f.read())
    f.close()
  except:
      feed = {}
  return feed

def set_feed(feed):
  last_updated_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "+00:00"
  feed['lastUpdated'] = last_updated_time
  f = open(os.path.join(APP_FEED, 'feed.json'), 'w') 
  f.write(json.dumps(feed, indent=4)) 
  f.close()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

if __name__=="__main__":
  app.secret_key = SECRET_KEY
  app.run(host='0.0.0.0', debug=True, port=8080)
