#!/usr/bin/env python3
"""
BNG Blaster - BGP Convergence Report 

Author: Christian Giese

Copyright (C) 2020-2024, RtBrick, Inc.
SPDX-License-Identifier: BSD-3-Clause
"""
import argparse
import sys
import logging
import time
import json
import matplotlib.pyplot as plt
from collections import Counter
import bngblaster

DESCRIPTION = """
BNG Blaster - BGP Convergence Report
"""
LOG_LEVELS = {
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG
}
BLASTER_ARGS = {
    "logging": True,
    "logging_flags": [
        "bgp"
    ],
    "report_flags": [
        "streams"
    ],
    "report": True,
    "stream_config": "/tmp/streams.json"
}

def init_logging(log_level: int) -> logging.Logger:
    level = LOG_LEVELS[log_level]
    log = logging.getLogger()
    log.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter('[%(asctime)s][%(levelname)-7s] %(message)s')
    formatter.datefmt = '%Y-%m-%d %H:%M:%S'
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log

def generate_png(result_array):
    t = [x[0] for x in result_array]
    rx_1_active = [x[1] for x in result_array]
    rx_1_added = [x[2] for x in result_array]
    rx_1_deleted = [x[3] for x in result_array]
    rx_2_active = [x[4] for x in result_array]
    rx_2_added = [x[5] for x in result_array]
    rx_2_deleted = [x[6] for x in result_array]

    fig, ax = plt.subplots()
    ax.plot(t, rx_1_active, label="rx1-active") 
    ax.plot(t, rx_1_added, label="rx1-added") 
    ax.plot(t, rx_1_deleted, label="rx1-deleted") 
    ax.plot(t, rx_2_active, label="rx2-active") 
    ax.plot(t, rx_2_added, label="rx2-added") 
    ax.plot(t, rx_2_deleted, label="rx2-deleted") 
    ax.grid()
    ax.legend()
    fig.set_size_inches(20, 10)
    fig.savefig("result.png", dpi=100)

def bgp_update(bbl: bngblaster.bngblaster, local_address: str, update_file=None, timeout=60):
    arguments = {"local-ipv4-address": local_address}
    if update_file:
        arguments["file"] = update_file
        bbl.command("bgp-raw-update", arguments)

    for _ in range(int(timeout/3)):
        time.sleep(3)
        try: 
            response = bbl.command("bgp-sessions", arguments)
            for session in response["bgp-sessions"]: 
                if session["state"] == "established" and \
                    session["raw-update-state"] == "done" and \
                    session["raw-update-start-epoch"] > 0 and \
                    session["raw-update-stop-epoch"] > 0:
                    # return session
                    return session
        except:
            pass

def log_interface_pps(bbl: bngblaster.bngblaster, log: logging.Logger):
    try:
        response = bbl.command("network-interfaces")
        m = "RX:"
        for i in response["network-interfaces"]:
            m += " %s %s PPS" % (i["name"], i["rx-pps"])
        log.info(m)
    except:
        pass

# ==== #
# MAIN #
# ==== #

def main():
    # parse arguments
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('--host', type=str, required=True, help="BNG Blaster Controller")
    parser.add_argument('--port', type=int, default=8001, help="BNG Blaster Controller Port")
    parser.add_argument('--instance', type=str, default="convergence", help="BNG Blaster Controller Instance")
    parser.add_argument('--rx1ip', type=str, default="192.0.2.194", help="RX1 local IP")
    parser.add_argument('--rx2ip', type=str, default="192.0.2.202", help="RX2 local IP")
    parser.add_argument('--timeout', type=int, default=120, help='Max convergence time expected')
    parser.add_argument('--log-level', type=str, default='info', choices=LOG_LEVELS.keys(), help='logging Level')

    args = parser.parse_args()
    log = init_logging(args.log_level)

    log.info("Init BNG Blaster test: %s", args.instance)
    bbl = bngblaster.bngblaster(args.host, args.port, args.instance)
    log.info("BNG Blaster URL: %s", bbl.base_url)
    bbl.create("blaster.json")
    bbl.start(BLASTER_ARGS)
    log.info("BNG Blaster status: %s", bbl.status())

    log.info("Wait for BGP updates from RX1")
    session = bgp_update(bbl, args.rx1ip)
    t1 = session["raw-update-start-epoch"]
    t2 = 0
    t3 = 0
    log.info("Send BGP updates from RX2")
    session = bgp_update(bbl, args.rx2ip, "/tmp/rx2.bgp")
    log.info("Verify traffic streams")

    response = bbl.command("stream-stats")
    total_streams = response["stream-stats"]["total-flows"]

    for _ in range(int(args.timeout/3)):
        time.sleep(3)
        log_interface_pps(bbl, log)
        response = bbl.command("stream-stats")
        verified = response["stream-stats"]["verified-flows"]
        log.info("Streams verifed: %s/%s", verified, total_streams)
        if total_streams == verified:
            break
    else:
        log.error("Failed to verify all traffic streams")
        bbl.stop()
        return

    # wait some time
    log.info("Wait %s seconds", 30)
    time.sleep(10)
    log_interface_pps(bbl, log)
    time.sleep(10)
    log_interface_pps(bbl, log)
    time.sleep(10)
    log_interface_pps(bbl, log)

    log.info("Withdraw prefixes from RX1")
    session = bgp_update(bbl, args.rx1ip, "/tmp/rx1-withdraw.bgp")
    t2 = session["raw-update-start-epoch"]

    log.info("Wait %s seconds", args.timeout)
    for _ in range(int(args.timeout/3)):
        time.sleep(3)
        log_interface_pps(bbl, log)

    log.info("Withdraw prefixes from RX2")
    session = bgp_update(bbl, args.rx2ip, "/tmp/rx2-withdraw.bgp")
    t3 = session["raw-update-start-epoch"]

    log.info("Wait %s seconds", args.timeout)
    for _ in range(int(args.timeout/3)):
        time.sleep(3)
        log_interface_pps(bbl, log)

    log.info("Stop test")
    bbl.stop()
    for _ in range(12):
        time.sleep(10)
        if bbl.status() == "stopped":
            break

    time.sleep(30)
    log.info("Download report")
    bbl.download("run_report.json")

    # load JSON report 
    log.info("Load JSON report file run_report.json")
    with open("run_report.json", "r") as json_file:
        data = json.load(json_file)

    # get test dudaration from report
    duration = data["report"].get("test-duration", 300)

    # init counter
    rx_1_first_epoch = Counter()
    rx_1_last_epoch = Counter()
    rx_2_first_epoch = Counter()
    rx_2_last_epoch = Counter()

    # iterate over all streams
    for stream in data["report"]["streams"]:
        rx_1_first_epoch[stream["rx-first-epoch"]-t1] += 1
        rx_1_last_epoch[stream["rx-interface-changed-epoch"]-t1] += 1
        rx_2_first_epoch[stream["rx-interface-changed-epoch"]-t1] += 1
        rx_2_last_epoch[stream["rx-last-epoch"]-t1] += 1

    # generate result array for line graph
    result_array = []

    rx_1_active = 0
    rx_1_added = 0
    rx_1_deleted = 0
    rx_2_active = 0
    rx_2_added = 0
    rx_2_deleted = 0

    c1 = 0
    c2 = 0
    c3 = 0

    for x in range(duration):
        rx_1_active += rx_1_first_epoch[x]
        rx_1_added = rx_1_first_epoch[x]
        rx_1_deleted = rx_1_last_epoch[x]

        if rx_1_last_epoch[x] > 0 and rx_1_active >= rx_1_last_epoch[x]:
            rx_1_active -= rx_1_last_epoch[x]

        rx_2_active += rx_2_first_epoch[x]
        rx_2_added = rx_2_first_epoch[x]
        rx_2_deleted = rx_2_last_epoch[x]

        if rx_2_last_epoch[x] > 0 and rx_2_active >= rx_2_last_epoch[x]:
            rx_2_active -= rx_2_last_epoch[x]

        result_array.append((x, rx_1_active, rx_1_added, rx_1_deleted, rx_2_active, rx_2_added, rx_2_deleted))

        if c1 == 0 and rx_1_active == total_streams:
            c1 = x
        if c2 == 0 and rx_2_active == total_streams:
            c2 = x - (t2 - t1)
        if c3 == 0 and c2 > 0 and rx_2_active == 0:
            c3 = x - (t3 - t1)

    log.info("C1: %s seconds", c1)
    log.info("C2: %s seconds", c2)
    log.info("C3: %s seconds", c3)

    # generate output files
    generate_png(result_array)


if __name__ == "__main__":
    main()