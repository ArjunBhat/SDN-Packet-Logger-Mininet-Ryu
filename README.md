# SDN Packet Logger using Ryu and Mininet

## Problem Statement
Implement an SDN controller that captures packet headers, identifies protocol types, installs flow rules, and logs packet information.

## Objective
Demonstrate controller-switch interaction, match-action flow rules, and packet monitoring using Mininet and OpenFlow.

## Topology
Single switch (s1) connected to three hosts (h1, h2, h3)

## Tools Used
Mininet
Ryu Controller
OpenFlow 1.3
Open vSwitch
Python

## Execution Steps

Start controller:
ryu-manager --ofp-tcp-listen-port 6633 packet_logger.py

Start Mininet:
sudo mn --topo single,3 --mac \
--switch ovs,protocols=OpenFlow13 \
--controller remote,ip=127.0.0.1,port=6633

Run tests:
pingall
iperf
h3 iperf -s -u &
h1 iperf -c 10.0.0.3 -u

Check flow table:
sh ovs-ofctl -O OpenFlow13 dump-flows s1

## Test Scenarios

Scenario 1: Normal operation
Traffic flows successfully and controller logs packets.

Scenario 2: Failure scenario
Controller stopped → packet loss observed.

## Results
Packet headers captured successfully.
Protocols identified correctly.
Flow rules installed dynamically.
