# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import in_proto as inet
from ryu.app.ofctl.api import get_datapath
import time

'''
h1 h1-eth0:s1-eth1
h2 h2-eth0:s2-eth1
s1 lo:  s1-eth1:h1-eth0 s1-eth2:s3-eth1 s1-eth3:s4-eth1
s2 lo:  s2-eth1:h2-eth0 s2-eth2:s3-eth2 s2-eth3:s4-eth2
s3 lo:  s3-eth1:s1-eth2 s3-eth2:s2-eth2
s4 lo:  s4-eth1:s1-eth3 s4-eth2:s2-eth3
'''


class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.timestamp = 0
        self.state = 'up'

    def send_to_group(self, dp):
        '''
        Modify group entry message
        The controller sends this message to modify the group table of the datapath.
        '''
        ofp = dp.ofproto
        parser = dp.ofproto_parser
        
        # s1 and s2 should be added into a group
        # the groupAction should has two entries, but only one shall be taken
        # since the OFPGT_FF is used
        
        # when sending packets, duplicate it to both port
        # when receiving packets, only receive one
        
        # port2 has the priority
        watch_group = ofproto_v1_3.OFPQ_ALL
        
        # when sending packet, use group_id = 7
        buckets = []
        actions = [parser.OFPActionOutput(2)]
        buckets.append(parser.OFPBucket(watch_port=2,
                                        actions=actions))
    
        actions = [parser.OFPActionOutput(3)]
        buckets.append(parser.OFPBucket(watch_port=3,
                                        actions=actions))
        
        req = parser.OFPGroupMod(datapath=dp,
                                 type_=ofp.OFPGT_FF,
                                 group_id=7,
                                 buckets=buckets)
        dp.send_msg(req)
        
        # when receving, use another group, w/ group_id = 8
        buckets = []
        actions = [parser.OFPActionOutput(1)]
        buckets.append(parser.OFPBucket(watch_port=2,
                                        actions=actions))
    
        buckets.append(parser.OFPBucket(watch_port=3,
                                        actions=actions))
        
        req = parser.OFPGroupMod(datapath=dp,
                                 type_=ofp.OFPGT_FF,
                                 group_id=8,
                                 buckets=buckets)
        dp.send_msg(req)
        
        # help packet of s3 recover (for in_port=1)
        # port2 -> 2 port1 -> 1
        buckets = []
        actions = [parser.OFPActionOutput(2)]
        buckets.append(parser.OFPBucket(watch_port=2,
                                        actions=actions))
        # if port2 failed, goes to port1
        actions = [parser.OFPActionOutput(1)]
        buckets.append(parser.OFPBucket(actions=actions))
        req = parser.OFPGroupMod(datapath=dp,
                                 type_=ofp.OFPGT_FF,
                                 group_id=9,
                                 buckets=buckets)
        dp.send_msg(req)

        
        
    
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        
        # ==================== CORE PART FOR GROUP TABLE ===================
        
        # s1 lo:  s1-eth1:h1-eth0 s1-eth2:s3-eth1 s1-eth3:s4-eth1
        # s2 lo:  s2-eth1:h2-eth0 s2-eth2:s3-eth2 s2-eth3:s4-eth2
        # s3 lo:  s3-eth1:s1-eth2 s3-eth2:s2-eth2
        # s4 lo:  s4-eth1:s1-eth3 s4-eth2:s2-eth3
        
        if datapath.id == 1:
            # packets from host1 goes to group table
            self.send_to_group(datapath)
            actions = [parser.OFPActionGroup(group_id=7)]
            match = parser.OFPMatch(in_port=1)
            self.add_flow(datapath, 7, match, actions)

            # return entries
            actions = [parser.OFPActionGroup(group_id=8)]
            match = parser.OFPMatch(in_port=2)
            self.add_flow(datapath, 7, match, actions)

            actions = [parser.OFPActionGroup(group_id=8)]
            match = parser.OFPMatch(in_port=3)
            self.add_flow(datapath, 7, match, actions)
            
            # recover
            actions = [parser.OFPActionOutput(3)]
            match = parser.OFPMatch(in_port=2, eth_dst=0x2)
            self.add_flow(datapath, 8, match, actions)
            
            actions = [parser.OFPActionOutput(1)]
            match = parser.OFPMatch(in_port=3, eth_dst=0x1)
            self.add_flow(datapath, 8, match, actions)
        
        if datapath.id == 2:
            # packets from host1 goes to group table
            self.send_to_group(datapath)
            actions = [parser.OFPActionGroup(group_id=7)]
            match = parser.OFPMatch(in_port=1)
            self.add_flow(datapath, 7, match, actions)

            # return entries
            actions = [parser.OFPActionGroup(group_id=8)]
            match = parser.OFPMatch(in_port=2)
            self.add_flow(datapath, 7, match, actions)

            actions = [parser.OFPActionGroup(group_id=8)]
            match = parser.OFPMatch(in_port=3)
            self.add_flow(datapath, 7, match, actions)
            
            actions = [parser.OFPActionOutput(1)]
            match = parser.OFPMatch(in_port=3, eth_dst=0x2)
            self.add_flow(datapath, 8, match, actions)
            
        if datapath.id == 3:
            actions = [parser.OFPActionOutput(1)]
            match = parser.OFPMatch(in_port=2)
            self.add_flow(datapath, 7, match, actions)
            
            match = parser.OFPMatch(in_port=1)
            actions = [parser.OFPActionGroup(group_id=9)]
            self.add_flow(datapath, 7, match, actions)
        
        if datapath.id == 4:
            actions = [parser.OFPActionOutput(1)]
            match = parser.OFPMatch(in_port=2)
            self.add_flow(datapath, 7, match, actions)
            
            actions = [parser.OFPActionOutput(2)]
            match = parser.OFPMatch(in_port=1)
            self.add_flow(datapath, 7, match, actions)
        
        # ==================== CORE PART FOR GROUP TABLE ===================
        

    # ??????flow??????table?????????????????????????????????datapath???
    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    # ??????PackitIn?????????????????????MAIN_DISPATCHER????????????????????????????????????
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        # if ev.msg.msg_len < ev.msg.total_len:
            # self.logger.debug("packet truncated: only %s of %s bytes",
            #                   ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # in .match the **metainfo** of the packet is set
        in_port = msg.match['in_port']
        
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # ?????????lldp??????????????????
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = format(datapath.id, "d").zfill(16)
        self.mac_to_port.setdefault(dpid, {})

        # self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # src??????????????????????????????????????????src?????????flood
        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        # ????????????????????????table???????????????????????????flooding
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # If the destination MAC address is found, an entry is added to the flow table of the OpenFlow switch.
        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
                
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
