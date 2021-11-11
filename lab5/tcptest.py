#!/usr/bin/python
"""Simple example of setting network and CPU parameters  """
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSBridge
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import quietRun, dumpNodeConnections
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from sys import argv
import time
# It would be nice if we didn't have to do this:# pylint: disable=arguments-differ
class SingleSwitchTopo( Topo ):
    def build( self ):
        bandwidth = 100
        lossrate = 0.3
        switch1 = self.addSwitch('s1')
        switch2 = self.addSwitch('s2')
        host1 = self.addHost('h1', cpu=.25)
        host2 = self.addHost('h2', cpu=.25)
        self.addLink(host1, switch1, bw=bandwidth, delay='5ms', loss=0, use_htb=True)
        self.addLink(host2, switch2, bw=bandwidth, delay='5ms', loss=0, use_htb=True)
        self.addLink(switch1, switch2, bw=100, delay='200ms', loss=lossrate, use_htb=True)

class BtlneckTopo( Topo ):
    def build( self ):

        switch1 = self.addSwitch('s1')
        switch0 = self.addSwitch('s0')

        bandwidth = 200

        host0 = self.addHost('h0', cpu=.25)
        host1 = self.addHost('h1', cpu=.25)
        host2 = self.addHost('h2', cpu=.25)
        host3 = self.addHost('h3', cpu=.25)

        self.addLink(host0, switch0, bw=bandwidth, delay='5ms', loss=0, use_htb=True)
        self.addLink(host1, switch1, bw=bandwidth, delay='5ms', loss=0, use_htb=True)
        self.addLink(host2, switch1, bw=bandwidth, delay='5ms', loss=0, use_htb=True)
        self.addLink(host3, switch1, bw=bandwidth, delay='5ms', loss=0, use_htb=True)
        self.addLink(switch0, switch1, bw=bandwidth, delay='5ms', loss=0, use_htb=True)

def Test(tcp):
    "Create network and run simple performance test"
    topo = BtlneckTopo()
    net = Mininet( topo=topo, host=CPULimitedHost, link=TCLink, autoStaticArp=False )
    net.start()
    info( "Dumping host connections\n" )
    dumpNodeConnections(net.hosts)
    # set up tcp congestion control algorithm
    output = quietRun( 'sysctl -w net.ipv4.tcp_congestion_control=' + tcp )
    assert tcp in output
    h0, h1, h2, h3 = net.getNodeByName('h0', 'h1', 'h2', 'h3')
    h0.cmdPrint('iperf -s &')
    h1.cmdPrint('iperf -c 10.0.0.1 &')
    h2.cmdPrint('iperf -c 10.0.0.1 &')
    h3.cmdPrint('iperf -c 10.0.0.1 &')
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    # pick a congestion control algorithm, for example, 'reno', 'cubic', 'bbr', 'vegas', 'hybla', etc.
    tcp = 'reno'
    Test(tcp)