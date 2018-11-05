import ffmpeg
import io
import json
import os
import pprint
import subprocess
import time
import urllib2
from bs4 import BeautifulSoup

import ydl

cache_root = os.path.expanduser("~/.carrot/cache")
ydl_root = cache_root+'/ydl'
v_root = cache_root+'/v'
www_root = '/var/www/html'

if not os.path.exists(cache_root):
    os.makedirs(cache_root)
if not os.path.exists(ydl_root):
    os.makedirs(ydl_root)
if not os.path.exists(v_root):
    os.makedirs(v_root)

def run(cmd):
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return p.returncode

def init(channel, item):
    item['cn'] = channel['cn']
    item['mp4'] = cache_root+"/v/"+item['cn']+item['key']+".mp4"
    item['ydl_mp4'] = cache_root+'/ydl/'+item['key']+".mp4"
    item['ydl_jpg'] = cache_root+'/ydl/'+item['key']+".jpg"
    item['www_mp4'] = www_root+'/'+item['cn']+item['key']+".mp4"
    item['www_jpg'] = www_root+'/'+item['cn']+item['key']+".jpg"
    item['html_mp4'] = '/'+item['cn']+item['key']+".mp4"
    item['html_jpg'] = '/'+item['cn']+item['key']+".jpg"
    item.pop('error', None)

def download(item):
    if os.path.exists(item['ydl_jpg']) and \
       os.path.exists(item['ydl_mp4']):
        print(item["title"] + " already downloaded")
    else:
        print("Downloading " + item["title"])
        ydl.download("~/.carrot/cache/ydl/", item['key'])
    try:
        if not os.path.exists(item['ydl_jpg']):
            raise Exception('jpg not found')
        probe = ffmpeg.probe(item['ydl_mp4'])
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        item["width"] = int(video_stream['width'])
        item["height"] = int(video_stream['height'])
        item["duration"] = int(float(video_stream['duration']))
        item.pop('error', None)
    except Exception as e:
        print(e)
        item['error'] = 'download'
        raise Exception('download error')

def encode(item):
    if not os.path.exists(item['mp4']):
        print("Generating "+item['mp4'])
        cmd = 'ffmpeg -i ' + item['ydl_mp4'] + \
                ' -y -crf 40 -strict -2 -b:a 20k -ac 1 -ar 8000 -r 10 ' + \
                item['mp4']
        run(cmd)
    try:
        probe = ffmpeg.probe(item['mp4'])
        item['size'] = probe['format']['size']
        item.pop('error', None)
        if not os.path.exists(item['www_mp4']):
            os.link(item['mp4'], item['www_mp4'])
        if not os.path.exists(item['www_jpg']):
            os.link(item['ydl_jpg'], item['www_jpg'])
    except Exception as e:
        print(e)
        item['error'] = 'encode'
        raise Exception('encode error')

def main():

    os.nice(19) # super low priority so that ffmpeg won't impact apache

    template = "default"
    config_file = template+"_template/config.json"
    with open(config_file) as data_file:
        config = json.load(data_file)

    channels = config["channels"]
    for channel in channels:

        if os.path.exists("html.tmp"):
            print("Reusing cached html file ...")
            with open("html.tmp", "rb") as f:
                html = f.read()
        else:
            url = "https://www.youtube.com/channel/"+channel["id"]
            print("Downloading " + url + "...")
            html = urllib2.urlopen(url).read()
            tmp_file = open("html.tmp","w")
            tmp_file.write(html)
            tmp_file.close()
            print("Saved to cache file")

        soup = BeautifulSoup(html, "lxml")
        now = int(time.time())

        channel_index_file = channel["id"]+".json"
        index = {}
        try:
            if os.path.exists(channel_index_file):
                with open(channel_index_file) as f:
                    index = json.load(f)
                print(len(index), "items loaded")
        except Exception:
            pass

        i = 0
        for h3 in soup.find_all("h3", class_="yt-lockup-title"):
            href=unicode(h3.a['href'])
            if (len(href) == 20) and (href[0:9] == "/watch?v="):
                key=href[9:20]
                if not key in index:
                    title=h3.a.get_text()
                    published=now-i
                    index[key] = {'key':key, 'published':published, 'title':title}
                    print("Added: " + title)
                i = i+1
                if i >= channel["max"]:
                    break

        new_index = {}
        i = 0
        for item in sorted(index.values(), key=lambda x: x['published'], reverse=True):
            try:
                init(channel, item)
                download(item)
                encode(item)
                new_index[item['key']] = item
            except Exception:
                print(item['error'])
                pass

            i += 1
            if i >= channel["max"]:
                break

        html = ''
        for item in sorted(new_index.values(), key=lambda x: x['published'], reverse=True):
            html +='<div><a href="'+item['html_mp4']+'"><img src="'+item['html_jpg']+'" />'+item['title']+'</a></div>'

        print("One loop done." + html)

        template_index_html = template + '_template/www/index.html'
        with open(template_index_html, 'r') as f:
            template_index_data = f.read()
        template_index_data = template_index_data.replace('CARROT_INDEX', html)
        with open(www_root+'/index.html', 'w') as f:
            f.write(template_index_data.encode('utf8'))

        print('index written')

        with io.open(channel["id"]+".json", "w") as f:
            f.write(json.dumps(new_index, ensure_ascii=False, indent=4))

        print("New index written: " + str(len(new_index)) + " items");

main()
