#!/bin/bash
# NOTE: Replace eth0 with the actual TX interface, but remain the leading ":10", which refers to the VLAN
# defines in the blaster.json confiuration. 
bgpupdate -f rx1.bgp --local-pref 100 -n 192.0.2.194 -N 1 -p 11.0.0.0/24 -P 900000 --end-of-rib \
    -s streams.json \
    --stream-direction downstream \
    --stream-pps 1 \
    --stream-interface eth0:10

bgpupdate -f rx1-withdraw.bgp --local-pref 100 -n 192.0.2.194 -N 1 -p 11.0.0.0/24 -P 900000 --withdraw --end-of-rib
bgpupdate -f rx2.bgp --local-pref 10 -n 192.0.2.202 -N 1 -p 11.0.0.0/24 -P 900000 --end-of-rib
bgpupdate -f rx2-withdraw.bgp --local-pref 10 -n 192.0.2.202 -N 1 -p 11.0.0.0/24 -P 900000 --withdraw --end-of-rib