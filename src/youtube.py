from bs4 import BeautifulSoup
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


if __name__ == "__main__":
    unittest.main()






