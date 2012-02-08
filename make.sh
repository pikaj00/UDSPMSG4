#!/bin/sh
this_dir=`pwd`
read -p "[Y/N] make hub?: " qna
if [[ "$qna" == *Y* ]] || [[ "$qna" == *y* ]]; then
    echo "[Default] `cat env/this_ip`"
    read -p "[Enter] this ip: " this_ip
    [[ "$this_ip" == '' ]] && this_ip=`cat env/this_ip`

    echo "[Default] `cat env/hub_socket`"
    read -p "[Enter] /path/to/hub/socket: " hub_socket
    [[ "$hub_socket" == '' ]] && hub_socket=`cat env/hub_socket`

    echo "[Default] `cat env/remote_sockets`"
    read -p "[Enter] /remote/sockets/directory: " remote_sockets
    [[ "$remote_sockets" == '' ]] && remote_sockets=`cat env/remote_sockets`

    echo "[Proposed configuration]
        this ip: $this_ip
        /path/to/hub/socket: $hub_socket
        /remote/sockets/directory: $remote_sockets"

    read -p "[Y/N] use this configuration?: " qna
    if [[ "$qna" == *Y* ]] || [[ "$qna" == *y* ]]; then
        echo -n $this_ip>env/this_ip
        echo -n $hub_socket>env/hub_socket
        echo -n $remote_sockets>env/remote_sockets

        mkdir -p /service/udpmsg4.hub
        cp run.hub /service/udpmsg4.hub/run
        cp hub.py /service/udpmsg4.hub/hub.py
        cp udpmsg4.py /service/udpmsg4.hub/udpmsg4.py
        chmod +x /service/udpmsg4.hub/run
        [ -e /service/udpmsg4.hub/env ] || ( cd / ; ln -s $this_dir/env /service/udpmsg4.hub )

        mkdir -p /service/udpmsg4.client
        cp run.client /service/udpmsg4.client/run
        cp client.py /service/udpmsg4.client/client.py
        chmod +x /service/udpmsg4.client/run
        [ -e /service/udpmsg4.client/env ] || ( cd / ; ln -s $this_dir/env /service/udpmsg4.client )
    fi
fi

read -p "[Y/N] make peers?: " qna
if [[ "$qna" == *Y* ]] || [[ "$qna" == *y* ]]; then
    for this_peer in `ls peers` ; do
        mkdir -p /service/udpmsg4.$this_peer
        cp run.peer /service/udpmsg4.$this_peer/run
        cp peer.py /service/udpmsg4.$this_peer/peer.py
        chmod +x /service/udpmsg4.$this_peer/run
        [ -e /service/udpmsg4.$this_peer/env ] || ( cd / ; ln -s $this_dir/env /service/udpmsg4.$this_peer )
        [ -e /service/udpmsg4.$this_peer/$this_peer ] || ( cd / ; ln -s $this_dir/peers/$this_peer /service/udpmsg4.$this_peer/peer )
    done
fi
