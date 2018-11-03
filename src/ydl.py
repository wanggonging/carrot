from __future__ import unicode_literals
import youtube_dl

class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading')

ydl_opts = {
    'format' : 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec':'mp3',
        'preferredquality':'48',
    }],
    'logger':MyLogger(),
    'progress_hooks':[my_hook],
}

def download(key):

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([key])

