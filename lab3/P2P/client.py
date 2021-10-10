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
FILESIZE = params["FILESIZE"]
PACKETSIZE = params["PACKETSIZE"]
PORT = params["PORT"]
MAX_FILE = params["MAX_FILE"]
FILE_OVER_FLOW = params["FILE_OVER_FLOW"]

# NEED TO ACQUIRE ALL CHUNKS FROM OTHER CLIENTS
NR_CHUNK = params["NR_HOST"]

# get the valid filename to save in local directory
def getfilename():
    for i in range(MAX_FILE):
        if os.path.exists("save%d.txt" % i):
            i += 1
        else:
            return "save%d.txt" % i
    return FILE_OVER_FLOW

class listenThread(threading.Thread):
    pass

def get_local_ip():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    
# two jobs, give out local chunks, download remote chunk
if __name__ == '__main__':
    localip = get_local_ip()