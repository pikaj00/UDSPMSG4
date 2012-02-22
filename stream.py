#!/usr/bin/env python
import sys, os, select, collections
from hashlib import *
import socket

selections=select.select
pathhub=(sys.argv[1])
PID=str(os.getpid())
os.write(2,'stream.py '+PID+' starting '+os.getenv('TCPREMOTEIP')+':'+os.getenv('TCPREMOTEPORT')+'\n')
pathstream=sys.argv[2]+'/'+PID
stream=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)

try:
    os.remove(pathstream)
except:
    pass

stream.setblocking(0)
stream.bind(pathstream)
streamfd=stream.fileno()

CLIENT_QUEUE=[]
SERVER_QUEUE=[]
SHA512_CACHE=collections.deque([],4096)
while 1:
    readable=selections([0,streamfd],[],[],1)[0]
    if streamfd in readable:
        try:
            packet_length=0
            packet=stream.recv(65536)
            packet_length=(ord(packet[:1:])*256)+ord(packet[1:2:])
        except:
            pass
        if packet_length==0:
            os.write(2,'stream.py: '+PID+' connection to server died\n')
            os.remove(pathstream)
            break
        elif packet_length!=len(packet[2::]):
            os.write(2,'stream.py: '+PID+' connection to server died\n')
            os.remove(pathstream)
            break
        else:
            checksum=sha512(packet).digest()
            if not checksum in SHA512_CACHE:
                CLIENT_QUEUE+=[packet]
                SHA512_CACHE+=[checksum]
                os.write(2,'stream.py: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')

    if 0 in readable:
        try:
            packet_length=0
            packet=os.read(0,2)
            packet_length=(ord(packet[:1:])*256)+ord(packet[1:2:])
            while len(packet[2::])!=packet_length:
                packet+=os.read(0,packet_length-len(packet[2::]))
        except:
            pass
        if packet_length==0:
            os.write(2,'stream.py: '+PID+' connection to client died\n')
            os.remove(pathstream)
            break
        elif packet_length!=len(packet[2::]):
            os.write(2,'stream.py: '+PID+' connection to client died\n')
            os.remove(pathstream)
            break
        else:
            checksum=sha512(packet).digest()
            if not checksum in SHA512_CACHE:
                SERVER_QUEUE+=[packet]
                SHA512_CACHE+=[checksum]
                os.write(2,'stream.py: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')

    if len(CLIENT_QUEUE)!=0:
        write_length=0
        packet=CLIENT_QUEUE[0]
        packet_length=len(packet)
        while packet_length!=write_length:
            try:
                write_length=os.write(1,packet[write_length::])
            except:
                break
        if packet_length==write_length:
            CLIENT_QUEUE=CLIENT_QUEUE[1::]
            os.write(2,'stream.py: '+PID+' successful write to client\n')
            os.write(2,'stream.py: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
        elif write_length>0:
            CLIENT_QUEUE[0]=packet[write_length::]
            os.write(2,'stream.py: '+PID+' could not write complete packet to client\n')
            os.write(2,'stream.py: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
        elif write_length==0:
            os.write(2,'stream.py: '+PID+' failed to write to client\n')
            os.write(2,'stream.py: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')

    if len(SERVER_QUEUE)!=0:
        write_length=0
        packet=SERVER_QUEUE[0]
        packet_length=len(packet)
        while packet_length!=write_length:
            try:
                write_length=stream.sendto(packet[write_length::],pathhub)
            except:
                break
        if packet_length==write_length:
            SERVER_QUEUE=SERVER_QUEUE[1::]
            os.write(2,'stream.py: '+PID+' successful write to server\n')
            os.write(2,'stream.py: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
        elif write_length>0:
            SERVER_QUEUE[0]=packet[write_length::]
            os.write(2,'stream.py: '+PID+' could not write complete packet to server\n')
            os.write(2,'stream.py: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
        elif write_length==0:
            os.write(2,'stream.py: '+PID+' failed to write to server\n')
            os.write(2,'stream.py: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
