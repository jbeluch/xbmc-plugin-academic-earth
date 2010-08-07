#!/usr/bin/env python
#OCW class
from urllib import quote_plus
from cStringIO import StringIO
import urllib2
import urlparse
import asyncore, socket
import xbmc
import xbmcgui
import xbmcplugin

class XBMCVideoPlugin(object):
    argv0 = None
    argv1 = None
    
    def __init__(self, argv0, argv1):
        self.xbmc = xbmc
        self.xbmcgui = xbmcgui
        self.xbmcplugin = xbmcplugin
        self.argv0 = argv0
        self.argv1 = int(argv1)
        self.dp = None
        
    def add_videos(self, lis, end=True):
        _lis = [self._make_directory_item(li, False) for li in lis]
        self.xbmcplugin.addDirectoryItems(self.argv1, _lis, len(_lis))
        if end == True: 
            self.xbmcplugin.endOfDirectory(self.argv1, cacheToDisc=True)        
    
    def add_dirs(self, dirs, end=True):
        _dirs = [self._make_directory_item(d, True) for d in dirs]
        self.xbmcplugin.addDirectoryItems(self.argv1, _dirs, len(_dirs))
        if end == True: 
            self.xbmcplugin.endOfDirectory(self.argv1, cacheToDisc=True)

    def _make_directory_item(self, diritem, isFolder=True):
        if isFolder:
            url = '%s?url=%s&mode=%s' % (self.argv0, quote_plus(diritem.get('url', '')), diritem.get('mode'))
        else:
            url = diritem.get('url')
        li = self.xbmcgui.ListItem(diritem.get('name'))
        if 'info' in diritem.keys(): li.setInfo('video', diritem.get('info'))
        if 'icon' in diritem.keys(): li.setIconImage(diritem.get('icon'))
        if 'tn' in diritem.keys(): li.setThumbnailImage(diritem.get('tn'))
        return (url, li, isFolder)
               
    def play_video(self, url, info=None):
        li = self.xbmcgui.ListItem('Lecture')
        if info: li.setInfo('video', info)
        self.xbmc.Player(self.xbmc.PLAYER_CORE_MPLAYER).play(url, li)

    def _urljoin(self, url):
        return urlparse.urljoin(self.base_url, url)

"""The below class is taken from:
    http://docs.python.org/library/asyncore.html#asyncore-example-basic-http-client

It is a way to download lots of different resources asynchronously so the plugin
directories can load faster 
"""
class HTTPClient(asyncore.dispatcher):

    def __init__(self, url, dp=None):
        self.url = url
        self.parsed_url = urlparse.urlparse(url)
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        #xbmc's current version of the python interpreter doesn't include named tuple attributes,
        #so use index instead of attribute 'netloc'
        self.connect((self.parsed_url[1], 80))
        self.write_buffer = 'GET %s HTTP/1.0\r\n\r\n' % self.url
        self.read_buffer = StringIO() 
        self.dp = dp

    def handle_read(self):
        data = self.recv(8192)
        self.read_buffer.write(data)

    def handle_write(self):
        sent = self.send(self.write_buffer)
        self.write_buffer = self.write_buffer[sent:]

    def handle_close(self):
        if self.dp:
            self.dp.increment(line3=self.parsed_url[2])
        self.close()

    def writable(self):
        return (len(self.write_buffer) > 0)

"""The below class is meant to extend functionality for the xbmcgui.DialogProgress class
It adds an increment() method, which updates the percentage of progress for one event, 
the step size is calculated by dividing 100 by the number of events to complte """
class DialogProgress(xbmcgui.DialogProgress):

    def __init__(self, heading, line1='', line2='', line3='', num_steps=None):
        xbmcgui.DialogProgress.__init__(self)
        self.lines = [line1, line2, line3]
        self.create(heading, *self.lines)
        self.update(0)
        self.num_steps = num_steps
        self.step = 0
        self.progress = 0
        if self.num_steps != None:
            self.step = int(100 / self.num_steps)
    
    def increment(self, num_incr_steps=1, line1=None, line2=None, line3=None):
        if line1 != None: self.lines[0] = line1
        if line2 != None: self.lines[1] = line2
        if line3 != None: self.lines[2] = line3
        self.progress += (num_incr_steps * self.step)
        self.update(self.progress, *self.lines)

def async_urlread(url_list, dp=None):
    #get list of httpclients
    #http_clients = map(HTTPClient, url_list)
    http_clients = [HTTPClient(url, dp) for url in url_list]
    #run the syncore loop and download all the urls
    asyncore.loop()
    #return a list of the responses
    return [c.read_buffer.getvalue() for c in http_clients]

def urlread(url):
    f = urllib2.urlopen(url)
    page_contents = f.read()
    f.close()
    return page_contents

def parse_qs(qs):
    if len(qs) < 1: return {}
    return dict([p.split('=') for p in qs.strip('?').split('&')])    
