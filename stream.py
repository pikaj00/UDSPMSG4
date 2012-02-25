#!/usr/bin/env python
import sys, os, select, collections
from hashlib import *
import socket

selections=select.select
pathhub=(sys.argv[1])
PID=str(os.getpid())
CLIENT='CLIENT=['+str(os.getpid())+'@'+os.getenv('TCPREMOTEIP')+':'+os.getenv('TCPREMOTEPORT')+']'
pathstream=sys.argv[2]+'/'+PID
stream=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)

try:
    os.remove(pathstream)
except:
    pass

stream.setblocking(0)
stream.bind(pathstream)
streamfd=stream.fileno()

TIMEOUT=1
READ_TIME=0
WRITE_TIME=0
CLIENT_QUEUE=[]
SERVER_QUEUE=[]
SHA512_CACHE=collections.deque([],4096)
while 1:
    os.write(2,'stream.py: '+CLIENT+' TIMEOUT=['+str(TIMEOUT)+'] READ_TIME=['+str(READ_TIME)+'] WRITE_TIME=['+str(WRITE_TIME)+'] CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
    TIMEOUT=1.0/(1+len(CLIENT_QUEUE)+len(SERVER_QUEUE)+READ_TIME+WRITE_TIME)
    readable=selections([0,streamfd],[],[],TIMEOUT)[0]
    if len(CLIENT_QUEUE)+len(SERVER_QUEUE)==0:
        WRITE_TIME=0
        READ_TIME=0
    else:
        if WRITE_TIME!=0:
            WRITE_TIME-=1
        if READ_TIME!=0:
            READ_TIME-=1

    if streamfd in readable:
        try:
            READ_TIME+=1
            packet_length=0
            packet=stream.recv(65536)
            packet_length=(ord(packet[:1:])*256)+ord(packet[1:2:])
        except:
            pass
        if packet_length==0 or len(packet)<=2:
            os.write(2,'stream.py: '+CLIENT+' connection to server died\n')
            os.remove(pathstream)
            break
        elif packet_length!=len(packet[2::]):
            os.write(2,'stream.py: '+CLIENT+' fatal protocol error from server\n')
            os.remove(pathstream)
            break
        else:
            checksum=sha512(packet).digest()
            if not checksum in SHA512_CACHE:
                CLIENT_QUEUE+=[packet]
                SHA512_CACHE+=[checksum]
                os.write(2,'stream.py: '+CLIENT+' successful read from server\n')

    if 0 in readable:
        try:
            packet=''
            packet_length=0
            packet=os.read(0,2)
            packet_length=(ord(packet[:1:])*256)+ord(packet[1:2:])
            while packet_length!=len(packet[2::]):
                READ_TIME+=1
                if 0 in selections([0],[],[],READ_TIME)[0]:
                    buffer=os.read(0,packet_length-len(packet[2::]))
                    if buffer!='':
                        packet+=buffer
                    else:
                        break
        except:
            pass
        if packet_length==0 or len(packet)<=2:
            os.write(2,'stream.py: '+CLIENT+' connection to client died\n')
            os.remove(pathstream)
            break
        elif packet_length!=len(packet[2::]):
            os.write(2,'stream.py: '+CLIENT+' fatal protocol error from client\n')
            os.remove(pathstream)
            break
        else:
            checksum=sha512(packet).digest()
            if not checksum in SHA512_CACHE:
                SERVER_QUEUE+=[packet]
                SHA512_CACHE+=[checksum]
                os.write(2,'stream.py: '+CLIENT+' successful read from client\n')

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
            CLIENT_QUEUE=CLIENT_QUEUE[1::]
            os.write(2,'stream.py: '+CLIENT+' successful write to client\n')
        elif write_length>0:
            CLIENT_QUEUE[0]=packet[write_length::]
            os.write(2,'stream.py: '+CLIENT+' could not write complete packet to client\n')
            break
        elif write_length==0:
            os.write(2,'stream.py: '+CLIENT+' failed to write to client\n')
            break

    while len(SERVER_QUEUE)!=0:
        write_length=0
        packet=SERVER_QUEUE[0]
        packet_length=len(packet)
        while packet_length!=write_length:
            try:
                write_length=stream.sendto(packet[write_length::],pathhub)
            except:
                break
        if packet_length==write_length:
            WRITE_TIME+=1
            SERVER_QUEUE=SERVER_QUEUE[1::]
            os.write(2,'stream.py: '+CLIENT+' successful write to server\n')
        elif write_length>0:
            SERVER_QUEUE[0]=packet[write_length::]
            os.write(2,'stream.py: '+CLIENT+' could not write complete packet to server\n')
            break
        elif write_length==0:
            os.write(2,'stream.py: '+CLIENT+' failed to write to server\n')
            break
