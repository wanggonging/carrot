import os
#from dateutil import parser
import time
import json

def to_seconds(t):
    return time.mktime(t.timetuple())

def count(table, line):
    tokens = line.split(' ')
    status=tokens[8]
    if status == '200':
        #time=tokens[3][1:]
        #t = parser.parse(time.replace(':',' ',1))
        #timestamp = to_seconds(t)
        path=tokens[6]
        tmp=path.find('?')
        if tmp!=-1:
            path=path[0:tmp]
        if (-1 != path.find('.mp4') or -1 != path.find('.mp3')):
            key=path[3:14]
            if key in table:
                table[key] += 1
            else:
                table[key] = 1

class Clicks:
    def __init__(self, json_file, log_file):
        self.json_file = json_file
        self.log_file = log_file
        self.data = {}
        try:
            with open(json_file) as f:
                self.data = json.load(f)
        except Exception:
            pass
        if not 'clicks' in self.data: self.data['clicks'] = {}
        self.handle = open(self.log_file, "r")
        self.lines = 0
        self.read_to_end()

    def read_to_end(self):
        while True:
            line = self.handle.readline()
            if not line: break
            if not 'marker' in self.data: self.data['marker'] = line
            count(self.data['clicks'], line)
            self.lines+=1
        self.size=os.path.getsize(self.log_file)

    def update(self):
        new_size = os.path.getsize(self.log_file)
        if self.size > new_size:
            self.size = 0
            self.handle = open(self.log_file, "r")
        self.read_to_end()

    def get_clicks(self, key):
        if key in self.data['clicks']:
            return self.data['clicks'][key]
        else:
            return 0

    def __del__(self):
        self.handle.close()

def dump(c):
    print(c.data['marker'])
    for item in c.data['clicks']:
        print(item + ' ' + str(c.data['clicks'][item]))


def main():
    print("Parsing ...")
    c = Clicks("clicks.json", "/var/log/apache2/access.log")
    c.update()
    print("Dumping ...")
    dump(c)
    print("get_clicks() returns: " + str(c.get_clicks('uO2FLayVaz8')))
    del c

if __name__ == "__main__":
	main()
