#!/usr/bin/env python3

"""
Copyright (c) 2023, Miquel Massot
All rights reserved.
Licensed under the GPLv3 License.
See LICENSE.md file in the project root for full license information.
"""

import argparse
import logging

from pyvoyis import Configuration, VoyisAPI
from pyvoyis.tools.custom_logger import setup_logging


def main():
    parser = argparse.ArgumentParser(
        description="Run a TCP client to send messages to Voyis API"
    )
    parser.add_argument("--ip", type=str, help="IP address of the Voyis API")
    parser.add_argument("--port", type=int, help="Port of the Voyis API")
    parser.add_argument("--log_path", type=str, help="Path to save the log file")
    parser.add_argument(
        "-c, --config", dest="config", type=str, help="Path to the configuration file"
    )
    args = parser.parse_args()

    config = Configuration(args.config)

    if args.log_path:
        config.log_path = args.log_path

    setup_logging(config.log_path)
    log = logging.getLogger("VoyisROS")
    log.info("Starting Voyis API client")

    if args.ip:
        log.info("Using provided IP address: %s", args.ip)
        config.ip_address = args.ip
    if args.port:
        log.info("Using provided port: %s", args.port)
        config.port = args.port

    api = VoyisAPI(config)
    api.request_acquisition()
    api.run()


if __name__ == "__main__":
    main()
