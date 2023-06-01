"""
Copyright (c) 2023, Miquel Massot
All rights reserved.
Licensed under the GPLv3 License.
See LICENSE.md file in the project root for full license information.
"""

from pyvoyis.messages import API500Message


class API500Command:
    def __init__(
        self, command, needs_payload=False, timeout_s=0, expected_response=None
    ):
        self.command = command
        self.payload = None
        self.needs_payload = needs_payload
        self.timeout_s = timeout_s
        self.expected_response = ["AckRsp"]
        if expected_response is not None:
            self.expected_response += expected_response

    def to_str(self):
        msg = API500Message(message=self.command)
        if self.needs_payload and self.payload is None:
            raise Exception("Command {} needs a payload".format(self.command))
        if self.needs_payload and self.payload is not None:
            msg.payload = self.payload
        return msg.to_str()
