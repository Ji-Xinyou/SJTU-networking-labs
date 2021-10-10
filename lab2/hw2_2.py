from mininet.link import TCLink
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, info


class myTopo( Topo ):
    def build(self, **opts):
        # hosts and switches added
        h1, h2, h3 = [ self.addHost( h ) for h in ('h1', 'h2', 'h3') ]
        s1, s2, s3 = [ self.addSwitch( s ) for s in ('s1', 's2', 's3') ]

        # switches wired up
        self.addLink(s1, s2, bw=10, loss=5)
        self.addLink(s1, s3, bw=10, loss=5)

        # hosts and switches wired up
        for (h, s) in [(h1, s1), (h2, s2), (h3, s3)]:
            self.addLink(h, s)

def perf():
    topo = myTopo()
    net = Mininet( topo=topo, 
                   waitConnected=True,
                   link=TCLink )
    net.start()
    h1, h2, h3 = net.getNodeByName('h1', 'h2', 'h3')

    info("*** NOW START IPERF BETWEEN HOSTS\n")
    for _h1, _h2 in [ (h1, h2), (h2, h3), (h1, h3) ]:
        net.iperf( hosts=(_h1, _h2), l4Type='TCP' )
    info("*** IPERF ENDS\n")
    
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    perf()
