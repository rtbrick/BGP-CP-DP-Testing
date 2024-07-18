# BGP CP/DP Testing with Open Source Tools

This project demonstrates how to measure the convergence between the BGP Control-Plane (CP) and the Data-Plane (DP) using the open-source tool BNG Blaster. By utilizing BNG Blaster, we can analyze and monitor the time it takes for routing changes to propagate from the control-plane, where BGP updates occur, to the data-plane, where actual data packet forwarding happens.

## CP/DP Test Methodology

![test](test.png)

In the BNG Blaster setup, a traffic stream is established for each prefix. Each traffic stream includes multiple timestamps:

+ The timestamp **rx-first-epoch** tracks the time of the first packet received on one of the RX interfaces.
+ The timestamp **rx-interface-changed-epoch** tracks the time if a packet is received on a different interface than the previous packet of the same stream.
+ The timestamp **rx-last-epoch** tracks the time of the last packet received.

Based on these timestamps, BNG Blaster calculates the CP/DP convergence time.

The following events and their corresponding timestamps are derived:

+ **T1**: Start sending BGP update from RX1
+ **T2**: Start sending BGP withdraw from RX1
+ **T3**: Start sending BGP withdraw from RX2
+ **S1**: All streams received on RX1 (most recent `rx-first-epoch`)
+ **S2**: All streams received on RX2 (most recent `rx-interface-changed-epoch`)
+ **S3**: No streams received on RX2 (most recent `rx-last-epoch`)

Using these timestamps, the convergence times are calculated as follows:

+ `C1 = S1 - T1`  Initial Convergence Time
+ `C2 = S2 - T2`  Switchover from RX1 to RX2
+ `C3 = S3 - T3`  Delete Time

The initial convergence time (C1) represents the delay between the BGP update started from RX1 and the reception of all streams on RX1. The switchover time (C2) measures the transition period during which streams switch from being received on RX1 to RX2. Finally, the delete time (C3) captures the duration until no streams are received on RX2 after the BGP withdraw is initiated from RX2.

## Prepare Test

+ [Install BNG Blaster](https://rtbrick.github.io/bngblaster/install.html) version 0.8.48 or newer togteher with the [BNG Blaster Controller](https://rtbrick.github.io/bngblaster/controller.html).
+ Replace the example interfaces `eth0-2` in the files `generate_routes.sh` and `blaster.json` with the actual interfaces used for `TX`, `RX1` and `RX2`.
+ Execute the script `generate_routes.sh` (this may takes a few minutes).
+ Copy the generated files to the server where the BNG Blaster controller is running:

```
scp *.bgp <user>@<blaster-controller>:/tmp/
scp streams.json <user>@<blaster-controller>:/tmp/
```

This example uses the address block `192.0.2.0/24`. This block is defined as "TEST-NET-1" by
[RFC5735](https://datatracker.ietf.org/doc/html/rfc5735).

## Run Test

```
$ ./convergence.py --help
usage: convergence.py [-h] --host HOST [--port PORT] [--instance INSTANCE] [--rx1ip RX1IP] [--rx2ip RX2IP] [--timeout TIMEOUT]
                      [--log-level {warning,info,debug}]

BNG Blaster - BGP Convergence Report

options:
  -h, --help            show this help message and exit
  --host HOST           BNG Blaster Controller
  --port PORT           BNG Blaster Controller Port
  --instance INSTANCE   BNG Blaster Controller Instance
  --rx1ip RX1IP         RX1 local IP
  --rx2ip RX2IP         RX2 local IP
  --timeout TIMEOUT     Max convergence time expected
  --log-level {warning,info,debug}
                        logging Level

$ ./convergence.py --host <blaster-controller>
```
