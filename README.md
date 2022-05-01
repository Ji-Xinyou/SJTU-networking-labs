# SJTU-networking-labs

This repo is for saving, if you want to read the code, they are not designed to be long-termly maintained so they are relatively hard to read.
If you have any problem, welcome to make it a **issue**.

Lab3 is the most fun, it contains an implementation of a distributed P2P file transmission.
* The client and server are not necessary themselves, clients work as servers, servers also work as clients.
* The peer numbering is hard-coded, and the file is distributed by chunks also in a hard-coded mechanism.
  * DHT not used, distribution of chunk is hard-coded
The testing result shows that, P2P has great improvement on speed comparing to the normal ClientSever model.
