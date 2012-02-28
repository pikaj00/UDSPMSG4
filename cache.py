#!/usr/bin/env python
import sys, os, select, collections
from hashlib import *
import socket

selections=select.select
cache=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)

try:
    os.remove('socket')
except:
    pass

cache.setblocking(0)
cache.bind(socket)
cachefd=cache.fileno()
SHA512_CACHE=collections.deque([],512*1024)
while 1:
    query=selections([cachefd],[],[],1)[0]
    if query!=[]:
        packet,remote=cache.recvfrom(65536)
        checksum=sha512(packet).digest()
        if not checksum in SHA512_CACHE:
            SHA512_CACHE+=[checksum]
            cache.sendto('\x00',remote)
        else:
            cache.sendto('\x01',remote)
