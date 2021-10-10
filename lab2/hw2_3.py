from mininet.link import TCLink
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI

class myTopo( Topo ):
    def build(self, **opts):
        # hosts and switches added
        h1, h2, h3 = [ self.addHost( h ) for h in ('h1', 'h2', 'h3') ]
        s1, s2, s3 = [ self.addSwitch( s ) for s in ('s1', 's2', 's3') ]

        # switches wired up
        self.addLink(s1, s2, bw=10, loss=5)
        self.addLink(s1, s3, bw=10, loss=5)
        self.addLink(s2, s3, bw=10, loss=5)

        # hosts and switches wired up
        for (h, s) in [(h1, s1), (h2, s2), (h3, s3)]:
            self.addLink(h, s)

def pingtest():
    topo = myTopo()
    net = Mininet( topo=topo, 
                   waitConnected=True,
                   link=TCLink )
    net.start()
    # ping test, use h1 ping h2 in CLI
    # since loop between switches exists, ARP STORM happens
    # so no pkg can reach the dest, so we add flow rules by ovs-ofctl
    #! run the simu again and type 
    #! ** sudo sh fctl.sh ** in another shell
    # then ping between h1 and h2 again, pkgs should pass now
    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    pingtest()