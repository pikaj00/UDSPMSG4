#!/usr/bin/env python
import sys, os, select, collections
from hashlib import *
import socket

selections=select.select
cache=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)

try:
    os.remove(sys.argv[1]+'/cache')
except:
    pass

cache.setblocking(0)
cache.bind((sys.argv[1]+'/cache'))
cachefd=cache.fileno()
SHA512_CACHE=collections.deque([],512*1024)
while 1:
    query=selections([cachefd],[],[],1)[0]
    if query!=[]:
        write_length=0
        packet,remote=cache.recvfrom(65536)
        checksum=sha512(packet).digest()
        if not checksum in SHA512_CACHE:
            while write_length!=1:
                try:
                    write_length=cache.sendto('\x00',remote)
                except:
                    if os.path.exists(remote)==False:
                        break
            SHA512_CACHE+=[checksum]
        else:
            while write_length!=1:
                try:
                    write_length=cache.sendto('\x01',remote)
                except:
                    if os.path.exists(remote)==False:
                        break
