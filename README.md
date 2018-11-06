# Design Goal

<pre>
root@vultr:~# git clone https://github.com/wanggonging/carrot
root@vultr:~# chmod 700 carrot/carrot
root@vultr:~# carrot/carrot
... installing dependencies
... configuring apache2
... using template [default]
... starting carrot service
... done.
root@vultr:~# tail -f /var/log/carrot.log
... crawling channel WZ
... downloading wz.mp3
... downloading wz.mp4
... encoding wz.mp4
... updating template from https://github.com/wanggonging/carrot/default_template
... refreshing pages
... one loop done. Sleeping 60 seconds.^C
</pre>

# Files and folder structure

## Source files

- launch.sh	master script
- src\*.py      python scripts (config, download, encode, publish, etc.)
- *_template\*  template (config, webpage template)

## Cache files @ $HOME/.carrot

- cache/WZ_*.json		video index
- cache/v/WZ_*.mp4		video cache
- cache/v/WZ_*.jpg              resized thumbnail
- cache/ydl/key.mp4,key.jpg 	original video/thumbnail cache

## Web site layout @ /var/www/html

- index.html
- <random>/*.mp4,*.jpg

