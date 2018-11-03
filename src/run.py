import io
import json
import os
import pprint
import time
import urllib2
from bs4 import BeautifulSoup

import ydl

def main():

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
        i = 0
        now = int(time.time())

        channel_index_file = channel["id"]+".json"
        if os.path.exists(channel_index_file):
            with open(channel_index_file) as f:
                index = json.load(f)
            print(len(index), "items loaded")
        else:
            index = {}
        for h3 in soup.find_all("h3", class_="yt-lockup-title"):
            href=unicode(h3.a['href'])
            if (len(href) == 20) and (href[0:9] == "/watch?v="):
                key=href[9:20]
                if not key in index:
                    title=h3.a.get_text()
                    published=now-i
                    index[key] = {'key':key, 'published':published, 'title':title}
                    print("Added: " + title)
                #pprint.pprint(index[key])
                i = i+1

        print(len(index), " items after parsing new html")
        # dump to file
        #for item in sorted(index.values(), key=lambda x: x['published']):
        #    pprint.pprint(item)

        with io.open(channel["id"]+".json", "w") as f:
            f.write(json.dumps(index, ensure_ascii=False))

        i = 0
        for item in sorted(index.values(), key=lambda x: x['published'], reverse=True):
            print("Downloading " + item["title"])
            ydl.download(key)
            i += 1
            if i >= channel["max"]:
                break




main()
