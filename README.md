# Design Goal

<pre>
root@vultr:~# git clone https://github.com/wanggonging/carrot && chmod +x carrot/carrot && carrot/carrot
... installing dependencies
... configuring apache2
... using template [default]
... crawling channel WZ
... downloading wz.mp3
... encoding wz.mp4
... refreshing pages
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

