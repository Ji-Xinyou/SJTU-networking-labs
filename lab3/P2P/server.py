import socket
import os
import math
import threading
import json

with open("../macro.json", 'r') as f:
    params = json.load(f)
FILESIZE = params["FILESIZE"]
PACKETSIZE = params["PACKETSIZE"]
PORT = params["PORT"]
NR_THREAD = params["NR_THREAD"]
MAX_BACKLOG = params["MAX_BACKLOG"]
NR_HOST = params["NR_HOST"]
# The number of file is chunked into equals pieces to all hosts
NR_CHUNK = NR_HOST

def createfile(reps=10):
    '''
    n reps === 2^n lines
    means 2^n+1 * 32bytes

    reps: 10 -> 32KB
          15 -> 1MB
          17 -> 4MB
          20 -> 32MB
          22 -> 128MB
    '''
    os.system("cat /dev/null > file.txt")
    os.system("printf \"HelloHelloHello\nWorldWorldWorld\n\" -> file.txt;")
    for i in range(reps):
        os.system("cat file.txt file.txt > file2.txt && mv file2.txt file.txt")

def countreps(FILESIZE):
    n = int(math.log2(FILESIZE))
    return 15 + n

def getchunks():
    chunks = []
    with open("file.txt", 'r') as f:
        content = f.read() # binary
        totallen = len(content)
        eachlen = totallen // NR_CHUNK
        chunk = ""
        for i in range(NR_CHUNK - 1):
            chunk = content[i * eachlen: (i + 1) * eachlen]
            chunks.append(chunk)
        chunk = content[(NR_CHUNK - 1) * eachlen: ]
        chunks.append(chunk)
    return chunks

def getips():
    baseip = "10.0.0."
    ips = []
    for i in range(NR_HOST):
        # i = 0 -> h1 -> 10.0.0.2
        postfix = str(i + 2)
        ip = baseip + postfix
        ips.append(ip)
    return ips

def accept_and_transmit(chunks, ips):
    count = 1
    while(1):
        if count == 1:
            print("\n\nThis is the server, request your file please!\n")

        sock_trans, client_ip_tuple = sock_listn.accept()
        client_ip, _ = client_ip_tuple
        # default FILESIZE is 8MB, change it in macro.py
        chunkidx = ips.index(client_ip)
        chunk_to_send = chunks[chunkidx]
        chunksize_byte = len(chunk_to_send)

        count = 0
        while chunksize_byte != 0:
            content = chunk_to_send[count * PACKETSIZE: (count + 1) * PACKETSIZE]
            content = content.encode('utf8')
            sock_trans.send(content)
            chunksize_byte -= len(content)
            count += 1

        sock_trans.close()
        print("chunk sent done to %s" % client_ip)
        count += 1

class myThread(threading.Thread):
    def __init__(self, nr, chunks, ips):
        threading.Thread.__init__(self)
        self.nr = nr
        self.chunks = chunks
        self.ips = ips

    def run(self):
        print("Thread # %d starts" % self.nr)
        # do the real job
        accept_and_transmit(chunks, ips)

if __name__ == "__main__":
    rep = countreps(FILESIZE)
    createfile(reps=rep)
    chunks = getchunks() # containing same # of chunks with NR_HOST
    # each chunk is distributed to fixed client
    # ips[0] -> h1's ip
    # ips[1] -> h2's ip
    # ... etc.
    ips = getips()
    sock_listn = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock_listn.bind(("10.0.0.1", PORT)) # bind to localhost
    sock_listn.listen(MAX_BACKLOG)

    threads = []
    for i in range(NR_THREAD):
        newthread = myThread(i + 1, chunks, ips)
        threads.append(newthread)
    for thread in threads:
        thread.start()