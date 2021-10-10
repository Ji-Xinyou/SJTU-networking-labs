'''
In P2P model, client not only is just client, it also serve as a server
Having a socket to listen to requests for local file chunk is essential here
'''

import socket
import time
import os
import json
import threading

with open("../macro.json", 'r') as f:
    params = json.load(f)
FILESIZE        = params["FILESIZE"]
PACKETSIZE      = params["PACKETSIZE"]
NR_HOST         = params["NR_HOST"]
MAX_BACKLOG     = params["MAX_BACKLOG"]
MAX_FILE        = params["MAX_FILE"]
FILE_OVER_FLOW  = params["FILE_OVER_FLOW"]

# serverport is for requesting local chunk from server
SERVERPORT      = params["PORT"]

#* clientport is for
    #* listening from other clients and sent local chunk
    #* request remote chunk from other clients
CLIENTPORT      = params["P2P_CLIENT_PORT"]

# NEED TO ACQUIRE ALL CHUNKS FROM OTHER CLIENTS
NR_CHUNK        = params["NR_HOST"]

def getips():
    baseip = "10.0.0."
    ips = []
    for i in range(NR_HOST):
        # i = 0 -> h1 -> 10.0.0.2
        postfix = str(i + 2)
        ip = baseip + postfix
        ips.append(ip)
    return ips

# get the valid filename to save in local directory
def getfilename():
    for i in range(MAX_FILE):
        if os.path.exists("save%d.txt" % i):
            i += 1
        else:
            return "save%d.txt" % i
    return FILE_OVER_FLOW

def get_local_ip():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)

def calc_size_each_chunk():
    totalsize = FILESIZE
    totalchunk = NR_CHUNK
    each_chunksize_int = totalsize // totalchunk
    chunk_size = []
    for i in range(NR_CHUNK - 1):
        chunk_size.append(each_chunksize_int)
        totalsize -= each_chunksize_int
    chunk_size.append(totalsize)
    return chunk_size

class listenThread(threading.Thread):
    '''
    ListenThread not only just serve the clients by transmitting the local chunk
    #! it first downloads the local chunk from server!
    #! remember to set the is_local_rdy to True after local trunk is ready
    '''

    def __init__(self, localip, ips, chunk_size, chunks):
        self.localip = localip
        self.ips = ips
        self.chunk_size = chunk_size
        self.chunks = chunks

    def run(self):
        print("I am the listening thread of %s", self.localip)
        #! first, request the local trunk
        sock_download = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock_download.connect(("10.0.0.1", SERVERPORT))

        selfchunkidx = self.ips.index(self.localip)        
        totalsize = self.chunk_size[selfchunkidx]
        while totalsize != 0:
            content = sock_download.rev(PACKETSIZE).decode()
            if content != "":
                chunks[selfchunkidx] += content
                totalsize -= len(content)
        # local trunk transfer done, set the global variable
        is_local_rdy = True
        sock_download.close()

        #! second, listen and transmit local trunk
        sock_listn = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock_listn.bind((self.localip, CLIENTPORT)) # bind to localhost
        sock_listn.listen(MAX_BACKLOG)

class downloadThread(threading.Thread):
    '''
    localip:  ip of the host running this thread
    ips:      all ips within the p2p topology
    nr_chunk: the number of chunks needed
    chunks: chunks to be saved in order
    '''
    def __init__(self, localip, ips, NR_CHUNK, chunk_size, chunks):
        # self.chunks is the chunks to be saves
        self.localip = localip
        # ips is all host's ips
        self.ips = ips
        self.chunks = chunks
        self.chunk_size = chunk_size
    
    def run(self):
        print("I am the downloading thread of %s", self.localip)

        chunkidx_needed = [i for i in range(NR_CHUNK)]
        selfchunkidx = self.ips.index(self.localip)
        chunkidx_needed.pop(selfchunkidx)

        # serial download
        #TODO: maybe upgrade it to parallel download?
        for idx in chunkidx_needed:
            sock_download = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            ip_to_connect = self.ips[idx]
            sock_download.connect((ip_to_connect, CLIENTPORT))
            totalsize = self.chunk_size[idx]
            while totalsize != 0:
                content = sock_download.recv(PACKETSIZE).decode()
                if content != "":
                    self.chunks[idx] += content
                    totalsize -= len(content)
            sock_download.close()

        filename = getfilename()
        # blocked here, until all trunks is ready
        while (is_local_rdy is False):
            pass

        if filename != FILE_OVER_FLOW:
            with open(filename, "w", encoding="utf-8") as f:
                for chunk in self.chunks:
                    f.write(chunk)
        


        

# two jobs, give out local chunks, download remote chunk
if __name__ == '__main__':
    localip = get_local_ip()
    #! chunks list is modified by threads!!!!!!!!!!!!!!
    #TODO remember to pass the chunks list to both threads!!!!!!!! 
    chunks = ["" for _ in range(NR_CHUNK)] 
    # listen thread works permanently (after the chunk is ready)
    # download thread works until all chunks are downloaded

    is_local_rdy = False
    
