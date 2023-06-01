"""
Copyright (c) 2023, Miquel Massot
All rights reserved.
Licensed under the GPLv3 License.
See LICENSE.md file in the project root for full license information.
"""

import inspect
import logging


def safe_get(dict, key):
    """Helper function to get a value from a dictionary

    The function quickly returns the value if it exists, otherwise it logs a warning
    with the name of the dictionary and the key that was not found.

    Parameters
    ----------
    dict : dict
        Dictionary to get the value from
    key : any
        Key to get the value from

    Returns
    -------
    value
        Value of the key if it exists, None otherwise
    """
    if key in dict:
        return dict[key]

    frame = inspect.currentframe()
    frame = inspect.getouterframes(frame)[1]
    string = inspect.getframeinfo(frame[0]).code_context[0].strip()
    args = string[string.find("(") + 1 : -1].split(",")
    names = []
    for i in args:
        if i.find("=") != -1:
            names.append(i.split("=")[1].strip())
        else:
            names.append(i)

    log = logging.getLogger("VoyisAPI")
    if len(names) == 1:
        log.warning(f"Key {names[0]} NOT FOUND")
    else:
        log.warning(f"Key{names[1]} in {names[0]} NOT FOUND")
    return None
