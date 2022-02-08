# SJTU-networking-labs

Most of the lab is not helpful for you to read.

Lab3 is fun, it is an implementation of a distributed P2P file transmission.
* The client and server are not necessary themselves, clients work as servers, servers also work as clients.
* The peer numbering is hard-coded, and the file is distributed by chunks also in a hard-coded mechanism.
  * If a auto distributed is needed, a DHT is needed (maybe also a trackor).

The testing result shows that, P2P has great improvement on speed comparing to the normal ClientSever model.
