#!/usr/bin/env python
import sys, os, select, collections
CLIENT='['+str(os.getpid())+'@'+os.getenv('TCPREMOTEIP')+':'+os.getenv('TCPREMOTEPORT')+']'
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
                            os.write(2,'ucspi-server2hub: '+CLIENT+' KEY ['+this_key+'] NOT IN ACCEPT\n')
                            return 0
            if config.accept[key]!=None:
                if key in kvps:
                    if config.accept[key]!=kvps[key]:
                        os.write(2,'ucspi-server2hub: '+CLIENT+' KEY/VALUE ['+key+'='+config.accept[key]+'] != ['+key+'='+kvps[key]+']\n')
                        return 0
        if None in config.accept.keys():
            if not config.accept[None] in kvps.values():
                os.write(2,'ucspi-server2hub: '+CLIENT+' VALUE ['+config.accept[None]+'] NOT IN PACKET\n')
                return 0

    if config.reject!={}:
        for key in config.reject.keys():
            if config.reject[key]==None:
                if key in kvps.keys():
                    os.write(2,'ucspi-server2hub: '+CLIENT+' KEY ['+key+'] IN REJECT\n')
                    return 0
            if config.reject[key]!=None:
                if key in kvps.keys():
                    if config.reject[key]==kvps[key]:
                        os.write(2,'ucspi-server2hub: '+CLIENT+' KEY/VALUE ['+key+'='+config.reject[key]+'] == ['+key+'='+kvps[key]+']\n')
                        return 0
        if None in config.reject.keys():
            if config.reject[None] in kvps.values():
                os.write(2,'ucspi-server2hub: '+CLIENT+' VALUE ['+config.reject[None]+'] IN PACKET\n')
                return 0
    return kvps

CLIENT_QUEUE=[]
SERVER_QUEUE=[]
SHA512_CACHE=collections.deque([],4096)
while 1:
    if config.mtime!=os.path.getmtime('config.py'):
        config.mtime=os.path.getmtime('config.py')
        reload(config)

    TIMEOUT=len(CLIENT_QUEUE)+len(SERVER_QUEUE)
    if TIMEOUT>128:
        TIMEOUT=128
    try:
        readable=selections([0,6],[],[],1/TIMEOUT)[0]
    except ZeroDivisionError:
        readable=selections([0,6],[],[],1)[0]

    if 6 in readable:
        try:
            packet=''
            packet_length=0
            packet=os.read(6,2)
            packet_length=(ord(packet[:1:])*256)+ord(packet[1:2:])
            while packet_length!=len(packet[2::]):
                buffer=os.read(6,packet_length-len(packet[2::]))
                if buffer!='':
                    packet+=buffer
                else:
                    break
        except:
            pass
        if packet_length==0 or len(packet)<=2:
            os.write(2,'ucspi-server2hub: '+CLIENT+' connection to server died\n')
            break
        elif packet_length!=len(packet[2::]):
            os.write(2,'ucspi-server2hub: '+CLIENT+' fatal protocol error from server\n')
            break
        kvps=udpmsg4.unframe(packet)
        checksum=sha512(packet).digest()
        if kvps==0:
            os.write(2,'ucspi-server2hub: '+CLIENT+' rejected protocol error from server\n')
        elif not checksum in SHA512_CACHE and filter(kvps)!=0:
            CLIENT_QUEUE+=[packet]
            SHA512_CACHE+=[checksum]
            os.write(2,'ucspi-server2hub: '+CLIENT+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')

    if 0 in readable:
        try:
            packet=''
            packet_length=0
            packet=os.read(0,2)
            packet_length=(ord(packet[:1:])*256)+ord(packet[1:2:])
            while packet_length!=len(packet[2::]):
                buffer=os.read(0,packet_length-len(packet[2::]))
                if buffer!='':
                    packet+=buffer
                else:
                    break
        except:
            pass
        if packet_length==0 or len(packet)<=2:
            os.write(2,'ucspi-server2hub: '+CLIENT+' connection to client died\n')
            break
        elif packet_length!=len(packet[2::]):
            os.write(2,'ucspi-server2hub: '+CLIENT+' fatal protocol error from client\n')
            break
        kvps=udpmsg4.unframe(packet)
        checksum=sha512(packet).digest()
        if kvps==0:
            os.write(2,'ucspi-server2hub: '+CLIENT+' rejected protocol error from client\n')
        elif not checksum in SHA512_CACHE and filter(kvps)!=0:
            SERVER_QUEUE+=[packet]
            SHA512_CACHE+=[checksum]
            os.write(2,'ucspi-server2hub: '+CLIENT+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')

    writeable=selections([],[1,7],[],0)[1]
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
            CLIENT_QUEUE=CLIENT_QUEUE[1::]
            os.write(2,'ucspi-server2hub: '+CLIENT+' successful write to client\n')
            os.write(2,'ucspi-server2hub: '+CLIENT+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
        elif write_length>0:
            os.write(2,'ucspi-server2hub: '+CLIENT+' could not write complete packet to client\n')
            os.write(2,'ucspi-server2hub: '+CLIENT+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
        elif write_length==0:
            CLIENT_QUEUE[0]=packet[write_length::]
            os.write(2,'ucspi-server2hub: '+CLIENT+' failed to write to client\n')
            os.write(2,'ucspi-server2hub: '+CLIENT+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
    elif not 1 in writeable and len(CLIENT_QUEUE)!=0:
        os.write(2,'ucspi-server2hub: '+CLIENT+' failed to write to client\n')
        os.write(2,'ucspi-server2hub: '+CLIENT+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')

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
            SERVER_QUEUE=SERVER_QUEUE[1::]
            os.write(2,'ucspi-server2hub: '+CLIENT+' successful write to server\n')
            os.write(2,'ucspi-server2hub: '+CLIENT+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
        elif write_length>0:
            SERVER_QUEUE[0]=packet[write_length::]
            os.write(2,'ucspi-server2hub: '+CLIENT+' could not write complete packet to server\n')
            os.write(2,'ucspi-server2hub: '+CLIENT+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
        elif write_length==0:
            os.write(2,'ucspi-server2hub: '+CLIENT+' failed to write to server\n')
            os.write(2,'ucspi-server2hub: '+CLIENT+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
    elif not 7 in writeable and len(SERVER_QUEUE)!=0:
        os.write(2,'ucspi-server2hub: '+CLIENT+' failed to write to server\n')
        os.write(2,'ucspi-server2hub: '+CLIENT+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
