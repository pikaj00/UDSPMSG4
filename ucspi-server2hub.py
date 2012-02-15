#!/usr/bin/env python
import sys, os, select, collections
PID='['+str(os.getpid())+']'
from hashlib import sha512
selections=select.select

sys.dont_write_bytecode=True
import config, udpmsg4
config.mtime=os.path.getmtime('config.py')

def filter(kvps):
    if kvps==0:
        return 0
    if config.accept!={}:
        for key in config.accept.keys():
            if config.accept[key]==None:
                if not key in kvps.keys():
                    for this_key in kvps.keys():
                        if not this_key in config.accept:
                            os.write(2,'ucspi-server2hub: '+PID+' KEY ['+this_key+'] NOT IN ACCEPT\n')
                            return 0
            if config.accept[key]!=None:
                if key in kvps:
                    if config.accept[key]!=kvps[key]:
                        os.write(2,'ucspi-server2hub: '+PID+' KEY/VALUE ['+key+'='+config.accept[key]+'] != ['+key+'='+kvps[key]+']\n')
                        return 0
        if None in config.accept.keys():
            if not config.accept[None] in kvps.values():
                os.write(2,'ucspi-server2hub: '+PID+' VALUE ['+config.accept[None]+'] NOT IN PACKET\n')
                return 0

    if config.reject!={}:
        for key in config.reject.keys():
            if config.reject[key]==None:
                if key in kvps.keys():
                    os.write(2,'ucspi-server2hub: '+PID+' KEY ['+key+'] IN REJECT\n')
                    return 0
            if config.reject[key]!=None:
                if key in kvps.keys():
                    if config.reject[key]==kvps[key]:
                        os.write(2,'ucspi-server2hub: '+PID+' KEY/VALUE ['+key+'='+config.reject[key]+'] == ['+key+'='+kvps[key]+']\n')
                        return 0
        if None in config.reject.keys():
            if config.reject[None] in kvps.values():
                os.write(2,'ucspi-server2hub: '+PID+' VALUE ['+config.reject[None]+'] IN PACKET\n')
                return 0
    return kvps

CLIENT_QUEUE=collections.deque([],128)
SERVER_QUEUE=collections.deque([],128)
SHA512_CACHE=collections.deque([],4096)
while 1:
    if config.mtime!=os.path.getmtime('config.py'):
        config.mtime=os.path.getmtime('config.py')
        reload(config)

    try:
        readable=selections([0,6],[],[],1/abs(len(CLIENT_QUEUE)-len(SERVER_QUEUE)))[0]
    except ZeroDivisionError:
        readable=selections([0,6],[],[],1)[0]

    if 6 in readable:
        packet=os.read(6,2)
        if not packet:
            os.write(2,'ucspi-server2hub: '+PID+' connection to server died\n')
            break
        packet_length=(ord(packet[:1:])*256)+ord(packet[1:2:])
        while len(packet[2::])!=packet_length:
            packet+=os.read(6,packet_length-len(packet[2::]))
        if not packet:
            os.write(2,'ucspi-server2hub: '+PID+' connection to server died\n')
            break
        kvps=filter(udpmsg4.unframe(packet))
        checksum=sha512(packet).digest()
        if kvps==0:
            os.write(2,'ucspi-server2hub: '+PID+' rejected protocol error from server\n')
        elif not checksum in SHA512_CACHE:
            CLIENT_QUEUE+=[packet]
            SHA512_CACHE+=[checksum]
            os.write(2,'ucspi-server2hub: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')

    if 0 in readable:
        packet=os.read(0,2)
        if not packet:
            os.write(2,'ucspi-server2hub: '+PID+' connection to client died\n')
            break
        packet_length=(ord(packet[:1:])*256)+ord(packet[1:2:])
        while len(packet[2::])!=packet_length:
            packet+=os.read(0,packet_length-len(packet[2::]))
        if not packet:
            os.write(2,'ucspi-server2hub: '+PID+' connection to client died\n')
            break
        kvps=filter(udpmsg4.unframe(packet))
        checksum=sha512(packet).digest()
        if kvps==0:
            os.write(2,'ucspi-server2hub: '+PID+' rejected protocol error from client\n')
        elif not checksum in SHA512_CACHE:
            SERVER_QUEUE+=[packet]
            SHA512_CACHE+=[checksum]
            os.write(2,'ucspi-server2hub: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')

    try:
        writeable=selections([],[1,7],[],1/abs(len(CLIENT_QUEUE)-len(SERVER_QUEUE)))[1]
    except ZeroDivisionError:
        writeable=selections([],[1,7],[],1)[1]

    if 1 in writeable and len(CLIENT_QUEUE)!=0:
        write_length=0
        packet=CLIENT_QUEUE[0]
        packet_length=len(packet)
        while packet_length!=write_length:
            try:
                write_length=os.write(1,packet[write_length::])
            except:
                break
        if packet_length==write_length:
            CLIENT_QUEUE.popleft()
            os.write(2,'ucspi-server2hub: '+PID+' successful write to client\n')
            os.write(2,'ucspi-server2hub: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
        elif write_length>0:
            CLIENT_QUEUE[0]=packet[write_length::]
            os.write(2,'ucspi-server2hub: '+PID+' could not write complete packet to client\n')
            os.write(2,'ucspi-server2hub: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
        elif write_length==0:
            os.write(2,'ucspi-server2hub: '+PID+' failed to write to client\n')
            os.write(2,'ucspi-server2hub: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')

    if 7 in writeable and len(SERVER_QUEUE)!=0:
        write_length=0
        packet=SERVER_QUEUE[0]
        packet_length=len(packet)
        while packet_length!=write_length:
            try:
                write_length=os.write(7,packet[write_length::])
            except:
                break
        if packet_length==write_length:
            SERVER_QUEUE.popleft()
            os.write(2,'ucspi-server2hub: '+PID+' successful write to server\n')
            os.write(2,'ucspi-server2hub: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
        elif write_length>0:
            SERVER_QUEUE[0]=packet[write_length::]
            os.write(2,'ucspi-server2hub: '+PID+' could not write complete packet to server\n')
            os.write(2,'ucspi-server2hub: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
        elif write_length==0:
            os.write(2,'ucspi-server2hub: '+PID+' failed to write to server\n')
            os.write(2,'ucspi-server2hub: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')