#!/usr/bin/env python
import sys, os, select, collections
PID='['+str(os.getpid())+']'
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
                            return 0
            if config.accept[key]!=None:
                if key in kvps:
                    if config.accept[key]!=kvps[key]:
                        return 0
        if None in config.accept.keys():
            if not config.accept[None] in kvps.values():
                return 0

    if config.reject!={}:
        for key in config.reject.keys():
            if config.reject[key]==None:
                if key in kvps.keys():
                    return 0
            if config.reject[key]!=None:
                if key in kvps.keys():
                    if config.reject[key]==kvps[key]:
                        return 0
        if None in config.reject.keys():
            if config.reject[None] in kvps.values():
                return 0
    return kvps

CLIENT_QUEUE=collections.deque([],128)
SERVER_QUEUE=collections.deque([],128)
while 1:
    if config.mtime!=os.path.getmtime('config.py'):
        config.mtime=os.path.getmtime('config.py')
        reload(config)

    try:
        readable=selections([0,6],[],[],1/abs(len(CLIENT_QUEUE)-len(SERVER_QUEUE)))[0]
    except ZeroDivisionError:
        readable=selections([0,6],[],[],1)[0]

    if 6 in readable:
        packet=os.read(6,65536)
        if not packet:
            os.write(2,'ucspi-server2hub: '+PID+' connection to server died\n')
            break
        kvps=filter(udpmsg4.unframe(packet))
        if kvps==0:
            os.write(2,'ucspi-server2hub: '+PID+' rejected packet from server\n')
        else:
            CLIENT_QUEUE+=[packet]
            os.write(2,'ucspi-server2hub: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+']\n')

    if 0 in readable:
        packet=os.read(0,65536)
        if not packet:
            os.write(2,'ucspi-server2hub: '+PID+' connection to client died\n')
            break
        kvps=filter(udpmsg4.unframe(packet))
        if kvps==0:
            os.write(2,'ucspi-server2hub: '+PID+' rejected packet from client\n')
        else:
            SERVER_QUEUE+=[packet]
            os.write(2,'ucspi-server2hub: '+PID+' SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')

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
                os.write(2,'ucspi-server2hub: '+PID+' failed to write to client\n')
                break
        if packet_length==write_length:
            CLIENT_QUEUE.popleft()
            os.write(2,'ucspi-server2hub: '+PID+' successful write to client\n')
            os.write(2,'ucspi-server2hub: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+']\n')
        elif write_length>0:
            CLIENT_QUEUE[0]=packet[write_length::]
            os.write(2,'ucspi-server2hub: '+PID+' could not write complete packet to client\n')
            os.write(2,'ucspi-server2hub: '+PID+' CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+']\n')

    if 7 in writeable and len(SERVER_QUEUE)!=0:
        write_length=0
        packet=SERVER_QUEUE[0]
        packet_length=len(packet)
        while packet_length!=write_length:
            try:
                write_length=os.write(7,packet[write_length::])
            except:
                os.write(2,'ucspi-server2hub: '+PID+' failed to write to server\n')
                break
        if packet_length==write_length:
            SERVER_QUEUE.popleft()
            os.write(2,'ucspi-server2hub: '+PID+' successful write to server\n')
            os.write(2,'ucspi-server2hub: '+PID+' SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
        elif write_length>0:
            SERVER_QUEUE[0]=packet[write_length::]
            os.write(2,'ucspi-server2hub: '+PID+' could not write complete packet to server\n')
            os.write(2,'ucspi-server2hub: '+PID+' SERVER_QUEUE=['+str(len(SERVER_QUEUE))+']\n')
