'''
This P2P implementation is hardcoded (file trunk in fixed host)
Only implemented for 4, 6 and 8 hosts P2P connection

One server, multiple clients

Connection:
    server connects to the first client
    each client connects to the client right next to it
'''

from mininet.link import TCLink
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost, Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.util import dumpNodeConnections, irange
import json

with open("../macro.json", 'r') as f:
    params = json.load(f)
NR_HOST = params["NR_HOST"]

class P2P_topo( Topo ):
    "P2P Model to simulate the performance"

    def build( self, nr_host, **opts ):
        
        # assert(nr_host in [4, 6, 8], "ONLY SUPPORT 4, 6, 8 CLIENTS!")

        # server is h0 - s0 pair
        server = self.addHost( 'h0', ip='10.0.0.1' )
        server_sw = self.addSwitch( 's0', stp=True )
        self.addLink( server, server_sw )

        # clients is h1 - s1 pair (or h2 - s2, etc.)
        clients = [ self.addHost( 'h%s' % h )
                                   for h in irange( 1, nr_host ) ]
        clients_sw = [ self.addSwitch( 's%s' % s, stp=True )
                                        for s in irange( 1, nr_host ) ]
        for client, client_sw in zip( clients, clients_sw ):
            self.addLink( client, client_sw )
        
        # wire up server and host1 (h0 and h1)
        self.addLink( 's0', 's1' )

        # wire up host1 to host2, host2 to host3, host3 to host4 ...
        for i in range( len(clients_sw) - 1 ):
            self.addLink( clients_sw[i], clients_sw[i + 1] )

def run( nr_host: int ):
    topo = P2P_topo( nr_host=nr_host )
    net = Mininet( topo=topo,
                   host=CPULimitedHost,
                   link=TCLink,
                   waitConnected=True )
    net.start()
    info( "Dumping host connections\n" )
    dumpNodeConnections(net.hosts)
    info( 'Starting doing your work!\n' )
    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    run( NR_HOST )