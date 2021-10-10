# h1 h1-eth0:s1-eth3
# h2 h2-eth0:s2-eth3
# h3 h3-eth0:s3-eth3
# s1 lo:  s1-eth1:s2-eth1 s1-eth2:s3-eth1 s1-eth3:h1-eth0
# s2 lo:  s2-eth1:s1-eth1 s2-eth2:s3-eth2 s2-eth3:h2-eth0
# s3 lo:  s3-eth1:s1-eth2 s3-eth2:s2-eth2 s3-eth3:h3-eth0
# c0

# lets cut one edge of the triangle s2 -- s3
# explanation: we only let pkg from h2(s1) goes to s1(h2)
# similar to s3, therefore 
# no pkg is going to take the path s2 -- s3 again
sudo ovs-ofctl add-flow s2 "in_port=3 actions=output:1"
sudo ovs-ofctl add-flow s2 "in_port=1 actions=output:3"
sudo ovs-ofctl add-flow s3 "in_port=3 actions=output:1"
sudo ovs-ofctl add-flow s3 "in_port=1 actions=output:3"