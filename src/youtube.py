from bs4 import BeautifulSoup
import json
import os
import pprint
import time
import urllib2
import unittest

def refresh_channel_index_with_html(index, html, channel_max):
    soup = BeautifulSoup(html, "lxml")
    now = int(time.time())

    i = 0
    for h3 in soup.find_all("h3", class_="yt-lockup-title"):
        href=unicode(h3.a['href'])
        if (len(href) == 20) and (href[0:9] == "/watch?v="):
            key=href[9:20]
            if not key in index:
                title=h3.a.get_text()
                published=now-i
                index[key] = {'key':key, 'published':published, 'title':title}
            i = i+1
            if i >= channel_max:
                break

def refresh_channel_index_with_apikey(index, apikey, channel_id, channel_max, channel_current_count):
    token=''
    now = int(time.time())
    i = 0
    while i < channel_max:
        url = 'https://www.googleapis.com/youtube/v3/search?key='+apikey+'&channelId='+channel_id+'&part=snippet,id&order=date&maxResults=50&pageToken='+token
        items = json.load(urllib2.urlopen(url))
        token=items.pop('nextPageToken', None)
        total=items['pageInfo']['totalResults']

        for item in items['items']:
            if 'videoId' in item['id']:
                key = item['id']['videoId']
                if not key in index:
                    title = item['snippet']['title']
                    published=now-i
                    index[key] = {'key':key, 'published':published, 'title':title}
                i = i+1
                if i>= channel_max:
                    break

        # Load only the first page if this channel has enough items
        if channel_current_count >= total or channel_current_count >= channel_max:
            break

        # Last page?
        if token == None:
            break

def refresh_channel_index(index, channel_id, channel_max):
  
    url = "https://www.youtube.com/channel/"+channel_id
    html = urllib2.urlopen(url).read()

    refresh_channel_index_with_html(index, html, channel_max)

class TestYoutube(unittest.TestCase):
    def test_refresh_channel_index(self):
        if os.path.exists("html.tmp"):
            print("Reusing cached html file ...")
            with open("html.tmp", "rb") as f:
                html = f.read()
        else:
            url = "https://www.youtube.com/channel/UCZ0oKRSK284apF3AxAw0ahg" # Xulin's channel
            print("Downloading " + url + "...")
            html = urllib2.urlopen(url).read()

            # Uncomment these if you need to fix the code, but don't want to download the url every time
            #tmp_file = open("html.tmp","w")
            #tmp_file.write(html)
            #tmp_file.close()
            #print("Saved to cache file")

        index = {}
        refresh_channel_index_with_html(index, html, 1)
        pprint.pprint(index)
        assert len(index) == 1
        assert index['_vZnN0EaRps'] != None


    def test_refresh_channel_index_with_apikey(self):
        apikey='AIzaSyCyaIc6wpatDoeuPVsET_2_-yh5arU27NA'
        channel_id='UCa6ERCDt3GzkvLye32ar89w'
        index={}
        refresh_channel_index_with_apikey(index, apikey, channel_id, 99999, 99999)
        assert(len(index)==50)
        index={}
        refresh_channel_index_with_apikey(index, apikey, channel_id, 99999, 10)
        i = 0
        for item in sorted(index.values(), key=lambda x: x['published'], reverse=True):
            print(str(i) + ': '+item['key']+' '+item['title'])
            i+=1
        assert(len(index)>100)
        assert('Subpk2MwYKk' in index)



if __name__ == "__main__":
    unittest.main()






