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
    'format' : '(mp4)[height<=400]',
    #'logger':MyLogger(),
    'outtmpl':'~/.carrot/cache/ydl/%(id)s.%(ext)s',
    'progress_hooks':[my_hook],
    'writethumbnail':True
}

def download(path, key):

    ydl_opts['outtmpl'] = path+"%(id)s.%(ext)s"
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([key])

def main():
    download('~/.carrot/cache/ydl/', 'elJwu3l3BO0')

if __name__ == "__main__":
    main()

