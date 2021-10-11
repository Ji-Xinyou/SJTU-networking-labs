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

class C_S_topo( Topo ):
    "A Client Server Model to simulate the performance"

    def build( self, nr_host, **_opts ):
        # a host is always an endpoint!

        # server is host0 with switch0 (h0 and s0)
        server = self.addHost( 'h0', ip='10.0.0.1' )
        server_sw = self.addSwitch( 's0' )
        # connect the server to its sw
        self.addLink( server, server_sw )

        # build hosts and give them each a sw
        clients = [ self.addHost( 'h%s' % h )
                                   for h in irange( 1, nr_host ) ]
        clients_sw = [ self.addSwitch( 's%s' % s )
                                        for s in irange( 1, nr_host ) ]
        for client, client_sw in zip( clients, clients_sw ):
            self.addLink( client, client_sw )
        
        #### TO BE FAIR, same topology as P2P topology ####
        # for client_sw in clients_sw:                    #
        #     self.addLink( server_sw, client_sw )        #
        #### TO BE FAIR, same topology as P2P topology ####

        # wire up server and host1 (h0 and h1)
        self.addLink( 's0', 's1' )

        # wire up host1 to host2, host2 to host3, host3 to host4 ...
        for i in range( len(clients_sw) - 1 ):
            self.addLink( clients_sw[i], clients_sw[i + 1] )
            
def run( nr_host: int ):
    topo = C_S_topo( nr_host=nr_host )
    net = Mininet( topo=topo,
                   host=CPULimitedHost,
                   link=TCLink,
                   waitConnected=True)
    net.start()
    info( "Dumping host connections\n" )
    dumpNodeConnections(net.hosts)
    info( 'Starting doing your work!\n' )
    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    run( NR_HOST )