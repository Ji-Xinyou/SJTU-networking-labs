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


# This function is used by multiple threads, be cautious about synchronization
def accept_transmit():
    count = 1
    while(1):
        if count == 1:
            print("\n\nThis is the server, request your file please!\n")
        # with each client's request, generate a new socket to handle the request
        # Described in https://www.scottklement.com/rpg/socktut/selectserver.html
        sock_trans, _ = sock_listn.accept()

        # default FILESIZE is 8MB, change it in macro.py
        TOTALBYTES = FILESIZE * 1024 * 1024
        with open("file.txt", "rb") as f:
            while TOTALBYTES != 0:
                content = f.read(PACKETSIZE)
                sock_trans.send(content)
                TOTALBYTES -= len(content)

        sock_trans.close()
        print("sent %d MB\n" % ( FILESIZE ))
        count += 1

class myThread(threading.Thread):
    def __init__(self, nr):
        threading.Thread.__init__(self)
        self.nr = nr
    def run(self):
        print("Thread # %d starts" % self.nr)
        accept_transmit()

if __name__ == '__main__':
    rep = countreps(FILESIZE)
    createfile(reps=rep)
    # server needs two sockets
    # one for listening to requests, another for transmission
    # In this lab, we choose both to be TCP socket
    
    sock_listn = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock_listn.bind(("10.0.0.1", PORT)) # bind to localhost
    sock_listn.listen(MAX_BACKLOG)

    # start multithread serving the clients
    # default # of threads is 4, change it in macro.py 
    # (more threads than this does not necessarily mean more throughput)
    threads = []
    for i in range(NR_THREAD):
        newthread = myThread(i + 1)
        threads.append(newthread)
    for thread in threads:
        thread.start()