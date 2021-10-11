import socket
from time import sleep
import os
import json

with open("../macro.json", 'r') as f:
    params = json.load(f)
FILESIZE = params["FILESIZE"]
PACKETSIZE = params["PACKETSIZE"]
PORT = params["PORT"]
MAX_FILE = params["MAX_FILE"]
FILE_OVER_FLOW = params["FILE_OVER_FLOW"]

def getfilename():
    for i in range(MAX_FILE):
        if os.path.exists("save%d.txt" % i):
            i += 1
        else:
            return "save%d.txt" % i
    return FILE_OVER_FLOW

if __name__ == '__main__':
    size_byte = FILESIZE * 1024 * 1024
    sock_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while sock_recv.connect_ex(("10.0.0.1", PORT)) != 0:
        sleep(1)

    # t_start = time.time()
    TTBYTES = size_byte
    buffer = ""
    while TTBYTES != 0:
        buf = sock_recv.recv(PACKETSIZE).decode()
        if buf != "":
            buffer += buf
            TTBYTES -= len(buf)

    filename = getfilename()
    if filename != FILE_OVER_FLOW:
        with open(filename, "w", encoding="utf-8") as f:
            for l in buffer:
                f.write(l)
    # t_end = time.time()
    sock_recv.close()
    print("I am a client! I have done my job!")

    # print("TOTAL TIME SPENT: %.4f seconds\n" % (t_end - t_start))