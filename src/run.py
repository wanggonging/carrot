import ffmpeg
import io
import json
import os
import pprint
import subprocess
import sys
import threading
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

def get_media_duration(media_file):
    try:
        probe = ffmpeg.probe(media_file)
        duration = float(probe['format']['duration'])
        print(media_file + ' duration: ' + str(duration))
    except Exception as e:
        duration = 0
    return duration

def assign(item):
    probe = ffmpeg.probe(item['ydl_mp4'])
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    try:
        item["width"] = int(video_stream['width'])
        item["height"] = int(video_stream['height'])
        item["duration"] = int(float(video_stream['duration']))
        item['creation_time'] = probe['format']['tags']['creation_time']
        item['shortname'] = item['cn']+'-'+item['creation_time'][5:10]
        item.pop('error', None)
    except Exception as e:
        print(e)
        pprint.pprint(probe)
        raise e

def download(item):
    if os.path.exists(item['ydl_jpg']) and \
        os.path.exists(item['ydl_mp4']):
        try:
            assign(item)
            return
        except Exception as e:
            print(item['ydl_mp4']+' might be corrupted. Downloading again.')
            pass

    print("Downloading " + item["title"])
    ydl.download("~/.carrot/cache/ydl/", item['key'])
    try:
        if not os.path.exists(item['ydl_jpg']):
            raise Exception('jpg not found')
        assign(item)
    except Exception as e:
        print('Exception: ' + str(e))
        item['error'] = 'download'
        raise Exception('download error')

def encode(item):
    duration = get_media_duration(item['ydl_mp4'])
    if os.path.exists(item['mp4']) and (get_media_duration(item['mp4']) < duration):
        print("Partial file "+item['mp4']+' '+item['title'])
    if os.path.exists(item['mp3']) and (get_media_duration(item['mp3']) < duration):
        print("Partial file "+item['mp3']+' '+item['title'])
    if not os.path.exists(item['mp4']) or get_media_duration(item['mp4']) < duration:
        print("Generating "+item['mp4']+' '+item['title'])
        cmd = 'ffmpeg -i ' + item['ydl_mp4'] + \
                ' -y -crf 35 -strict -2 -b:a 20k -ac 1 -ar 8000 -r 10 ' + \
                item['mp4']
        run(cmd)
    if not os.path.exists(item['mp3']) or get_media_duration(item['mp3']) < duration:
        print("Generating "+item['mp3']+' '+item['title'])
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
        item['mp4_raw_size'] = sizeof_fmt(os.path.getsize(item['ydl_mp4']))
        item['mp4_size']     = sizeof_fmt(os.path.getsize(item['mp4']))
        item['mp3_size']     = sizeof_fmt(os.path.getsize(item['mp3']))
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

g_template = 'default'
g_channels = {}
g_globalLock = threading.Lock()
g_apikey = None

class CrawlerThread (threading.Thread):
    def __init_(self):
        threading.Thread.__init__(self)
    def run(self):
        min_loop_time = 300  # seconds
        while True:
            start = time.time()
            crawler()
            end = time.time()
            if (end - start) < min_loop_time:
                time.sleep(min_loop_time - (end - start))

def crawler():
    current_channels = {}
    with g_globalLock:
        for c in g_channels:
            channel = g_channels[c]
            if channel['enabled']:
                current_channels[c] = channel
    for c in current_channels: crawl_one_channel(current_channels[c])

def crawl_one_channel(channel):
    print("one_channel: "+channel['name'])
    index = {}
    if g_apikey:
        youtube.refresh_channel_index_with_apikey(index, g_apikey, channel['id'], channel['max'], len(channel['index']))
    else:
        youtube.refresh_channel_index(index, channel['id'], channel['max'])
    i = 0
    for item in sorted(index.values(), key=lambda x: x['published'], reverse=True):
        try:
            init(channel, item)
            download(item)
            encode(item)
            with g_globalLock:
                channel['index'][item['key']] = item
        except Exception as e:
            print("Exception in crawler")
            print(e)
            pass
        print('Done: ' + item['title'])
        i += 1
        if i >= channel["max"]:
            break
    with g_globalLock:
        with io.open(channel['index_file'], "w") as f:
            f.write(json.dumps(channel['index'], ensure_ascii=False, indent=4))

def load_template():
    config_file = g_template+"_template/config.json"
    print('Loading ' + config_file)
    with open(config_file) as data_file:
        config = json.load(data_file)
    with g_globalLock:
        global g_apikey
        if 'apikey' in config:
            g_apikey=config['apikey']
        else:
            g_apikey=None
        for c in g_channels:
            g_channels[c].pop('enabled', None)
        for channel in config["channels"]:
            if not channel['id'] in g_channels:
                g_channels[channel['id']] = channel
                g_channels[channel['id']]['index'] = {}
                channel_index_file = cache_root+'/'+channel['cn']+channel['id']+'.json'
                g_channels[channel['id']]['index_file'] = channel_index_file
                g_channels[channel['id']]['index'] = {}
                try:
                    print('Loading '+channel_index_file)
                    if os.path.exists(channel_index_file):
                        with open(channel_index_file) as f:
                            g_channels[channel['id']]['index'] = json.load(f)
                except Exception:
                    pass
            else:
                g_channels[channel['id']].update(channel)
            g_channels[channel['id']]['enabled'] = True

def generate_html():
    run('rsync -av '+g_template+'_template/www/ /var/www/html') 
    merged_index = {}
    with g_globalLock:
        for c in g_channels:
            channel = g_channels[c]
            if channel['enabled']:
                for i in channel['index']:
                    item = channel['index'][i]
                    merged_index[item['key']] = item
        html = ''
        with io.open(g_template+'_template/www/index.ITEM', mode='r', encoding='utf-8') as f:
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

        with io.open(g_template+'_template/www/index', mode='r', encoding='utf-8') as f:
            template_index_html = f.read()

        template_index_html = template_index_html \
                        .replace('CARROT_INDEX', html) \
                        .replace('CARROT_NOW', time.strftime('%Y.%m.%d %H:%M:%S',time.localtime()))
        with open(www_root+'/index.html', 'w') as f:
            f.write(template_index_html.encode('utf8'))

def main():


    os.nice(19) # super low priority so that ffmpeg won't impact apache

    if len(sys.argv) > 1:
        global g_template
        g_template=sys.argv[1]
    print('Using template '+g_template)

    load_template()

    crawlerThread = CrawlerThread()
    crawlerThread.daemon = True
    crawlerThread.start()

    while True:
        generate_html()
        load_template()
        print('index.html updated. Sleeping ...')
        time.sleep(30)

main()
