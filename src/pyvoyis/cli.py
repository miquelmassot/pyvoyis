#!/usr/bin/env python3

"""
Copyright (c) 2023, Miquel Massot
All rights reserved.
Licensed under the GPLv3 License.
See LICENSE.md file in the project root for full license information.
"""

import argparse
import logging

from pyvoyis import VoyisAPI
from pyvoyis.tools.custom_logger import setup_logging


def main():
    parser = argparse.ArgumentParser(
        description="Run a TCP client to send messages to Voyis API"
    )
    parser.add_argument(
        "--ip", type=str, default="192.168.10.26", help="IP address of the Voyis API"
    )
    parser.add_argument("--port", type=int, default=4875, help="Port of the Voyis API")
    parser.add_argument(
        "--log_path", type=str, default="logs", help="Path to save the log file"
    )
    args = parser.parse_args()

    setup_logging(args.log_path)
    log = logging.getLogger("VoyisROS")
    # log.setLevel(logging.INFO)

    log.info("Starting Voyis client")

    api = VoyisAPI(args.ip, args.port)
    api.request_acquisition()
    api.run()


if __name__ == "__main__":
    main()
