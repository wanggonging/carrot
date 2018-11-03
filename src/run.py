import json
import os
import pprint
import urllib2
from bs4 import BeautifulSoup

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
        pprint.pprint(soup.title)


main()
