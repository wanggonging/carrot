import ffmpeg
import io
import json
import os
import pprint
import subprocess
import sys
import time

import ydl
import youtube

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

def sizeof_fmt(num, suffix=''):
    for unit in ['','K','M','G']:
        if abs(num) < 1024.0:
            return "%d%s%s" % (int(round(num)), unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'T', suffix)

def run(cmd):
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return p.returncode

def init(channel, item):
    item['cn'] = channel['cn']
    item['mp3'] = cache_root+"/v/"+item['cn']+item['key']+".mp3"
    item['mp4'] = cache_root+"/v/"+item['cn']+item['key']+".mp4"
    item['jpg'] = cache_root+"/v/"+item['cn']+item['key']+".jpg"
    item['ydl_mp4'] = cache_root+'/ydl/'+item['key']+".mp4"
    item['ydl_jpg'] = cache_root+'/ydl/'+item['key']+".jpg"
    item['www_mp3'] = www_root+'/'+item['cn']+item['key']+".mp3"
    item['www_mp4'] = www_root+'/'+item['cn']+item['key']+".mp4"
    item['www_mp4_raw'] = www_root+'/'+item['cn']+item['key']+"r.mp4"
    item['www_jpg'] = www_root+'/'+item['cn']+item['key']+".jpg"
    item['html_mp3'] = '/'+item['cn']+item['key']+".mp3"
    item['html_mp4'] = '/'+item['cn']+item['key']+".mp4"
    item['html_mp4_raw'] = '/'+item['cn']+item['key']+"r.mp4"
    item['html_jpg'] = '/'+item['cn']+item['key']+".jpg"
    item.pop('error', None)

def download(item):
    if os.path.exists(item['ydl_jpg']) and \
       os.path.exists(item['ydl_mp4']):
        pass
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
        item['creation_time'] = video_stream['tags']['creation_time']
        item['shortname'] = item['cn']+'-'+item['creation_time'][5:10]
        item.pop('error', None)
    except Exception as e:
        print(e)
        item['error'] = 'download'
        raise Exception('download error')

def encode(item):
    if not os.path.exists(item['mp4']):
        print("Generating "+item['mp4'])
        cmd = 'ffmpeg -i ' + item['ydl_mp4'] + \
                ' -y -crf 35 -strict -2 -b:a 20k -ac 1 -ar 8000 -r 10 ' + \
                item['mp4']
        run(cmd)
    if not os.path.exists(item['mp3']):
        print("Generating "+item['mp3'])
        cmd = 'ffmpeg -i ' + item['ydl_mp4'] + \
                ' -y -q:a 8 -map a ' + \
                item['mp3']
        run(cmd)
    if not os.path.exists(item['jpg']):
        print("Generating "+item['jpg'])
        cmd = 'convert ' + item['ydl_jpg'] + \
                ' -resize 64x36 ' + item['jpg']
        run(cmd)
    try:
        probe = ffmpeg.probe(item['mp4'])
        item['mp4_size'] = sizeof_fmt(int(probe['format']['size']))
        probe = ffmpeg.probe(item['ydl_mp4'])
        item['mp4_raw_size']=sizeof_fmt(int(probe['format']['size']))
        item['mp3_size']=sizeof_fmt(os.path.getsize(item['mp3']))
        if not os.path.exists(item['www_mp3']):
            os.link(item['mp3'], item['www_mp3'])
        if not os.path.exists(item['www_mp4']):
            os.link(item['mp4'], item['www_mp4'])
        if not os.path.exists(item['www_mp4_raw']):
            os.link(item['ydl_mp4'], item['www_mp4_raw'])
        if not os.path.exists(item['www_jpg']):
            os.link(item['jpg'], item['www_jpg'])
        item.pop('error', None)
    except Exception as e:
        print(e)
        item['error'] = 'encode'
        raise Exception('encode error')

def one_channel(merged_index, channel):

    print("one_channel: "+channel['name'])

    channel_index_file = cache_root+'/'+channel['cn']+channel['id']+'.json'
    index = {}
    try:
        if os.path.exists(channel_index_file):
            with open(channel_index_file) as f:
                index = json.load(f)
    except Exception:
        pass

    youtube.refresh_channel_index(index, channel['id'], channel['max'])

    new_index = {}
    i = 0
    for item in sorted(index.values(), key=lambda x: x['published'], reverse=True):
        try:
            init(channel, item)
            download(item)
            encode(item)
            new_index[item['key']] = item
            merged_index[item['key']] = item
        except Exception:
            print(item['error'])
            pass

        i += 1
        if i >= channel["max"]:
            break
    with io.open(channel_index_file, "w") as f:
        f.write(json.dumps(new_index, ensure_ascii=False, indent=4))

def main():

    os.nice(19) # super low priority so that ffmpeg won't impact apache

    if len(sys.argv) > 1:
        template=sys.argv[1]
    else:
        template = "default"

    while True:
        config_file = template+"_template/config.json"
        with open(config_file) as data_file:
            config = json.load(data_file)

        channels = config["channels"]
        merged_index = {}
        for channel in channels:
            one_channel(merged_index, channel)

        html = ''
        with io.open(template+'_template/www/index.html.ITEM', mode='r', encoding='utf-8') as f:
            template_index_html_ITEM = f.read()
        for item in sorted(merged_index.values(), key=lambda x: x['creation_time'], reverse=True):
            html += template_index_html_ITEM \
                .replace('CARROT_MP4_RAW_SIZE', item['mp4_raw_size']) \
                .replace('CARROT_MP4_SIZE', item['mp4_size']) \
                .replace('CARROT_MP3_SIZE', item['mp3_size']) \
                .replace('CARROT_MP4_RAW', item['html_mp4_raw']) \
                .replace('CARROT_MP4', item['html_mp4']) \
                .replace('CARROT_MP3', item['html_mp3']) \
                .replace('CARROT_JPG', item['html_jpg']) \
                .replace('CARROT_SHORTNAME', item['shortname']) \
                .replace('CARROT_TITLE', item['title'])

        with io.open(template+'_template/www/index.html', mode='r', encoding='utf-8') as f:
            template_index_html = f.read()

        template_index_html = template_index_html.replace('CARROT_INDEX', html)
        with open(www_root+'/index.html', 'w') as f:
            f.write(template_index_html.encode('utf8'))
        print('index.html updated. Sleeping ...')
        time.sleep(360)

main()
