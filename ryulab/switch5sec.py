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


class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.timestamp = 0
        self.state = 'up'

    def remove_table_flows(self, datapath, match, instructions):
        """
        Create OFP flow mod message to remove flows from table.
        """
        ofproto = datapath.ofproto
        flow_mod = datapath.ofproto_parser.OFPFlowMod(datapath=datapath,
                                                      command=ofproto.OFPFC_DELETE,
                                                      buffer_id=ofproto.OFPCML_NO_BUFFER,
                                                      out_port=ofproto.OFPP_ANY,
                                                      out_group=ofproto.OFPG_ANY,
                                                      match=match, 
                                                      instructions=instructions)
        return flow_mod
    
    
    def init_flow(self, datapath):
        """
        Removing all flow entries.
        Add the default flow entry then.
        """
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        empty_match = parser.OFPMatch()
        instructions = []
        flow_mod = self.remove_table_flows(datapath,
                                           empty_match, 
                                           instructions)
        datapath.send_msg(flow_mod)
        
        # add the init flow entry
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                            ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, empty_match, actions)

    def try_and_init_dp(self, dpid):
        dp = None
        while dp is None:
            dp = get_datapath(self, dpid)
            self.logger.info("Trying to get datapath w/ dpid: %d" % dpid)
        if dp is not None:
            self.init_flow(dp)
        return dp
    
    def goes_up_only(self, prio):
        
        # recover all
        dp_s1 = self.try_and_init_dp(dpid=1)
        dp_s2 = self.try_and_init_dp(dpid=2)
        dp_s3 = self.try_and_init_dp(dpid=3)
        dp_s4 = self.try_and_init_dp(dpid=4)
          
        # ============== modify s1 flowtable =================================
        # s1:1 only goes to s1:2 (s3)
        # all from port 1 goes to port 2
        parser = dp_s1.ofproto_parser
        ofproto = dp_s1.ofproto
        
        match = parser.OFPMatch(in_port=1)
        out_port = 2
        actions = [parser.OFPActionOutput(out_port)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, 
                                                actions)]
        mod = parser.OFPFlowMod(datapath=dp_s1,
                                priority=prio,
                                match=match,
                                instructions=inst)
        dp_s1.send_msg(mod)
        
        # all from port 2 goes to port 1
        match = parser.OFPMatch(in_port=2)
        out_port = 1
        actions = [parser.OFPActionOutput(out_port)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, 
                                                actions)]
        mod = parser.OFPFlowMod(datapath=dp_s1,
                                priority=prio,
                                match=match,
                                instructions=inst)
        dp_s1.send_msg(mod)
        # ============== modify s1 flowtable =================================

        # ============== s4 drop the packet ===================================================
        # get the s4's datapath and initialize it                   
        parser = dp_s4.ofproto_parser
        ofproto = dp_s4.ofproto
        
        match = parser.OFPMatch()
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_CLEAR_ACTIONS,
                                                [])]
        mod = parser.OFPFlowMod(datapath=dp_s4,
                                priority=prio,
                                match=match,
                                instructions=inst)
        dp_s4.send_msg(mod)
        # ============== s4 drop the packet ===================================================
    
    def goes_down_only(self, prio):
        
        # recover all
        dp_s1 = self.try_and_init_dp(dpid=1)
        dp_s2 = self.try_and_init_dp(dpid=2)
        dp_s3 = self.try_and_init_dp(dpid=3)
        dp_s4 = self.try_and_init_dp(dpid=4)
                    
        # ============== modify s1 flowtable =================================
        # s1:1 only goes to s1:2 (s3)
        # all from port 1 goes to port 2
        parser = dp_s1.ofproto_parser
        ofproto = dp_s1.ofproto
        match = parser.OFPMatch(in_port=1)
        out_port = 3
        actions = [parser.OFPActionOutput(out_port)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, 
                                                actions)]
        mod = parser.OFPFlowMod(datapath=dp_s1,
                                priority=prio,
                                match=match,
                                instructions=inst)
        dp_s1.send_msg(mod)
        
        # all from port 2 goes to port 1
        match = parser.OFPMatch(in_port=3)
        out_port = 1
        actions = [parser.OFPActionOutput(out_port)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, 
                                                actions)]
        mod = parser.OFPFlowMod(datapath=dp_s1, 
                                priority=prio, 
                                match=match, 
                                instructions=inst)
        dp_s1.send_msg(mod)
        # ============== modify s1 flowtable =================================

        # s3 drop the packet
        parser = dp_s3.ofproto_parser
        ofproto = dp_s3.ofproto
        match = parser.OFPMatch()
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_CLEAR_ACTIONS,
                                                [])]
        mod = parser.OFPFlowMod(datapath=dp_s3, 
                                priority=prio, 
                                match=match, 
                                instructions=inst)
        dp_s3.send_msg(mod)
    
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
        

    # 添加flow进入table，先产生事件，然后放进datapath中
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

    # 如果PackitIn事件发生，且在MAIN_DISPATCHER状态中，就调用下面的函数
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
        
        # ==================== CORE PART FOR SWITCHING PATH ===================
        
        # # set up the timestamp for controller
        # self.timestamp = time.time()
        # while(time.time() - self.timestamp < 5):
        #     pass 
        # self.timestamp = time.time()
        # # if the time is up, update the timestamp
        
        # # reverse the state and log the info for more info
        if datapath.id == 1 and time.time() - self.timestamp >= 5:
            if self.state == 'down':
                self.goes_up_only(2)
                self.state = 'up'
                self.logger.info("========== GOES UP ONLY ===========")
                self.timestamp = time.time()
            else:
                self.goes_down_only(2)
                self.state = 'down'
                self.logger.info("========== GOES DOWN ONLY ===========")
                self.timestamp = time.time()
            
        # ==================== CORE PART FOR SWITCHING PATH ===================
        
        # DEBUGING SESSION =====================================
        # self.goes_up_only(2)
        # self.goes_down_only(2)
        # self.goes_up_only(2)
        # ======================================================
        
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # 如果是lldp包，直接丢弃
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = format(datapath.id, "d").zfill(16)
        self.mac_to_port.setdefault(dpid, {})

        # self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # src的来源端口记录下来，防止发给src时再次flood
        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        # 如果目标的地址在table中，直接发出，否则flooding
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
