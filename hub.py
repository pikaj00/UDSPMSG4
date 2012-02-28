#!/usr/bin/env python
import sys, os, select, collections
from time import time
import socket

selections=select.select
PID=str(os.getpid())
HUBDIR=sys.argv[1]
HUBPATH=(sys.argv[1]+'/'+PID)
CACHEDIR=sys.argv[2]
CACHESOCK=sys.argv[2]+'/cache'
CACHEPATH=(sys.argv[2]+'/'+PID)
CLIENT='CLIENT=['+str(os.getpid())+'@'+os.getenv('TCPREMOTEIP')+':'+os.getenv('TCPREMOTEPORT')+']'
hub=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
cache=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
try:
    os.remove(HUBPATH)
except:
    pass

try:
    os.remove(CACHEPATH)
except:
    pass

hub.setblocking(0)
hub.bind(HUBPATH)
HUBFD=hub.fileno()

cache.setblocking(0)
cache.bind(CACHEPATH)
CACHEFD=cache.fileno()

LOOP_TIME=0
READ_TIME=0
WRITE_TIME=0
CLIENT_QUEUE=[]
SOCKET_QUEUE={}
REMOTE_QUEUE='[]'
while 1:
    TIME=time()
    TIMEOUT=1.0/(1+LOOP_TIME)
    REMOTE_SOCKS=os.listdir(HUBDIR)
    MAX_QUEUE=128*len(os.listdir(HUBDIR))
    os.write(2,'hub.py: '+CLIENT+' MAX_QUEUE=['+str(MAX_QUEUE)+'] TIMEOUT=['+str(TIMEOUT)+'] REMOTE_QUEUE='+REMOTE_QUEUE+'\n')
    readable=selections([0,HUBFD],[],[],TIMEOUT)[0]

    if HUBFD in readable:
        try:
            READ_TIME+=1
            packet_length=0
            packet,REMOTE=hub.recvfrom(65536)
            packet_length=(ord(packet[:1:])*256)+ord(packet[1:2:])
        except:
            pass
        if packet_length==0 or len(packet)<=2:
            os.write(2,'hub.py: '+CLIENT+' connection to '+REMOTE[len(HUBDIR)+1::]+' died\n')
        elif packet_length!=len(packet[2::]):
            os.write(2,'hub.py: '+CLIENT+' rejected protocol error from '+REMOTE[len(HUBDIR)+1::]+'\n')
        else:
            write_length=0
            while write_length!=len(packet):
                try:
                    write_length=cache.sendto(packet,CACHESOCK)
                except:
                    pass
            while 1:
                if len(selections([CACHEFD],[],[],TIMEOUT)[0])==1:
                    if cache.recv(1)=='\x00':
                        CLIENT_QUEUE+=[packet]
                        os.write(2,'hub.py: '+CLIENT+' successful read from '+REMOTE[len(HUBDIR)+1::]+'\n')
                    if len(CLIENT_QUEUE)<=MAX_QUEUE:
                        CLIENT_QUEUE=collections.deque(CLIENT_QUEUE,MAX_QUEUE)
                    break

    if 0 in readable:
        try:
            packet=''
            packet_length=0
            packet=os.read(0,2)
            packet_length=(ord(packet[:1:])*256)+ord(packet[1:2:])
            while packet_length!=len(packet[2::]):
                if 0 in selections([0],[],[],TIMEOUT)[0]:
                    buffer=os.read(0,packet_length-len(packet[2::]))
                    if buffer!='':
                        packet+=buffer
                    else:
                        break
        except:
            pass
        if packet_length==0 or len(packet)<=2:
            os.write(2,'hub.py: '+CLIENT+' connection to client died\n')
            os.remove(HUBPATH)
            os.remove(CACHEPATH)
            break
        elif packet_length!=len(packet[2::]):
            os.write(2,'hub.py: '+CLIENT+' fatal protocol error from client\n')
            os.remove(HUBPATH)
            os.remove(CACHEPATH)
            break
        else:
            os.write(2,'hub.py: '+CLIENT+' successful read from client\n')
            for REMOTE in REMOTE_SOCKS:
                if not HUBDIR+'/'+REMOTE in SOCKET_QUEUE and REMOTE!=PID:
                    SOCKET_QUEUE[HUBDIR+'/'+REMOTE]=collections.deque([],MAX_QUEUE)
                if HUBDIR+'/'+REMOTE in SOCKET_QUEUE and REMOTE!=PID:
                    SOCKET_QUEUE[HUBDIR+'/'+REMOTE]+=[packet]

    while len(CLIENT_QUEUE)!=0:
        write_length=0
        packet=CLIENT_QUEUE[0]
        packet_length=len(packet)
        while packet_length!=write_length:
            try:
                write_length=os.write(1,packet[write_length::])
            except:
                break
        if packet_length==write_length:
            WRITE_TIME+=1
            CLIENT_QUEUE.popleft()
            os.write(2,'hub.py: '+CLIENT+' successful write to client\n')
        elif write_length>0:
            CLIENT_QUEUE[0]=packet[write_length::]
            os.write(2,'hub.py: '+CLIENT+' could not write complete packet to client\n')
            break
        elif write_length==0:
            os.write(2,'hub.py: '+CLIENT+' failed to write to client\n')
            break

    if SOCKET_QUEUE!={}:
        DEQUE=[]
        REMOTE_QUEUE=''
        for REMOTE in SOCKET_QUEUE:
            DEQUE+=[REMOTE]
            if REMOTE!=HUBPATH:
                while len(SOCKET_QUEUE[REMOTE])!=0:
                    write_length=0
                    packet=SOCKET_QUEUE[REMOTE][0]
                    packet_length=len(packet)
                    while packet_length!=write_length:
                        try:
                            write_length=hub.sendto(packet[write_length::],REMOTE)
                        except:
                            break
                    if packet_length==write_length:
                        SOCKET_QUEUE[REMOTE].popleft()
                        os.write(2,'hub.py: '+CLIENT+' successful write to '+REMOTE[len(HUBDIR)+1::]+'\n')
                    elif write_length>0:
                        SOCKET_QUEUE[REMOTE][0]=packet[write_length::]
                        os.write(2,'hub.py: '+CLIENT+' could not write complete packet to '+REMOTE[len(HUBDIR)+1::]+'\n')
                        break
                    elif write_length==0:
                        os.write(2,'hub.py: '+CLIENT+' failed to write to '+REMOTE[len(HUBDIR)+1::]+'\n')
                        break
                if len(SOCKET_QUEUE[REMOTE])<=MAX_QUEUE:
                    SOCKET_QUEUE[REMOTE]=collections.deque(SOCKET_QUEUE[REMOTE],MAX_QUEUE)
                REMOTE_QUEUE+=REMOTE[len(HUBDIR)+1::]+'='+str(len(SOCKET_QUEUE[REMOTE]))+', '
        REMOTE_QUEUE='['+REMOTE_QUEUE[:len(REMOTE_QUEUE)-2:]+']'
        for REMOTE in DEQUE:
            if not os.path.exists(REMOTE):
                del SOCKET_QUEUE[REMOTE]
    else:
        REMOTE_QUEUE='[]'
    LOOP_TIME=time()-TIME
