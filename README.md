* Design goal

root@vultr:~# git clone https://github.com/wanggonging/carrot
root@vultr:~# chmod 700 carrot/launch.sh
root@vultr:~# carrot/launch.sh
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


* Files and folder structure

- launch.sh	master script
- src\*.py      python scripts (config, download, encode, publish, etc.)
- *_template\*  template (config, webpage template)


