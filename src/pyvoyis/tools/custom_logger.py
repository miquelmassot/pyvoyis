"""
Copyright (c) 2023, Miquel Massot
All rights reserved.
Licensed under the GPLv3 License.
See LICENSE.md file in the project root for full license information.
"""

import logging
import time
from pathlib import Path


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "[%(asctime)s][%(levelname)s]: %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logging(log_path):
    # Create log directory if it does not exist
    Path(log_path).mkdir(parents=True, exist_ok=True)
    # Create log filename with date and time
    log_file_name = time.strftime("%Y%m%d_%H%M%S") + "_voyis_api_client.log"

    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"  # noqa: E501

    # set up logging to file - see previous section for more details
    logging.basicConfig(
        level=logging.DEBUG,
        format=format_str,
        datefmt="%m-%d %H:%M",
        filename=(log_path + "/" + log_file_name),
        filemode="w",
    )
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # tell the handler to use this format
    console.setFormatter(CustomFormatter())
    # add the handler to the root logger
    logging.getLogger("").addHandler(console)
