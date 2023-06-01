"""
Copyright (c) 2023, Miquel Massot
All rights reserved.
Licensed under the GPLv3 License.
See LICENSE.md file in the project root for full license information.
"""

import asyncio
import json
import logging
import sys

if sys.version_info[:2] >= (3, 7):
    pass
else:
    pass


class API500ClientProtocol(asyncio.Protocol):
    def __init__(self, loop):
        self.log = logging.getLogger("API500ClientProtocol")
        self.transport = None
        self.queue = asyncio.Queue()
        self._ready = asyncio.Event()
        self.loop = loop
        self.task = self.loop.create_task(self._process_queue_loop())
        # Store received messages here
        self.received = []
        self.lock = asyncio.Lock()
        self.connected = False

    async def _process_queue_loop(self):
        """Send messages to the server as they become available."""
        await self._ready.wait()
        self.log.info("API500 client ready!")
        while True:
            message = await self.queue.get()
            self.transport.write(message.encode("utf-8"))
            self.log.debug("Message sent: \n{}".format(message))
            await asyncio.sleep(0.1)

    def connection_made(self, transport):
        """Upon connection send the message to the
        server

        A message has to have the following items:
            type:       subscribe/unsubscribe
            channel:    the name of the channel
        """
        self.transport = transport
        self.address = transport.get_extra_info("peername")

        self.log.debug("Connection made.")
        self._ready.set()
        self.connected = True

    async def send_message(self, data):
        """Feed a message to the sender coroutine."""
        await self.queue.put(data)

    async def process_data(self, data):
        # try to parse the data as json
        try:
            data = json.loads(data)
            if "message" not in data:
                return
            await self.lock.acquire()
            self.received.append(data)
            self.lock.release()
        except json.JSONDecodeError as e:
            self.log.error("ERROR: {}".format(e))
            self.log.error("Offending message:")
            self.log.error(data)
            return

    def data_received(self, data):
        """After sending a message we expect a reply
        back from the server

        The return message consist of three fields:
            type:           subscribe/unsubscribe
            channel:        the name of the channel
            channel_count:  the amount of channels subscribed to
        """
        data = data.decode("utf-8")
        # self.log.debug('Received: \n{}'.format(data))

        # Split data into JSON strings if "}{" is found
        objects = data.split("}{")

        # Add back the missing brackets
        if len(objects) > 1:
            objects[0] = objects[0] + "}"
            objects[-1] = "{" + objects[-1]
            for idx in range(1, len(objects) - 1):
                objects[idx] = "{" + objects[idx] + "}"

        # Process each object
        for idx, obj in enumerate(objects):
            self.log.debug(
                "Received split object {}: {}".format(idx, json.dumps(json.loads(obj)))
            )
            asyncio.ensure_future(self.process_data(obj))

    def connection_lost(self, error):
        if error:
            self.log.error("ERROR: {}".format(error))
        else:
            self.log.warning("The server closed the connection")
        self.connected = False


class API500Client:
    def __init__(self, ip, port, loop, task_set):
        self.ip = ip
        self.port = port
        self.protocol = None
        self.transport = None
        self.received = []
        self.loop = loop
        self.task_set = task_set
        self.log = logging.getLogger("API500Client")

    async def connect(self):
        self.log.info("Connecting to {} port {}".format(self.ip, self.port))
        self.protocol = API500ClientProtocol(self.loop)
        self.task_set.add(self.protocol.task)
        try:
            task = self.loop.create_task(self.do_connect())
            self.task_set.add(task)
        except ConnectionRefusedError as e:
            self.protocol.task.cancel()
            self.log.error("ERROR: {}".format(e))

    async def do_connect(self):
        while True:
            if not self.protocol.connected:
                try:
                    self.transport, _ = await self.loop.create_connection(
                        lambda: self.protocol, self.ip, self.port
                    )
                except OSError:
                    self.log.warning(
                        "Voyis API500 server is not online. Retrying in 5 seconds..."
                    )
            await asyncio.sleep(5)

    async def disconnect(self):
        self.log.info("Closing connection")
        self.transport.close()
        self.protocol.close()

    @property
    def connected(self):
        if self.protocol is None:
            return False
        return self.protocol.connected

    async def send_message(self, data):
        self.log.debug("Queuing message: {!r}".format(data))
        await self.protocol.send_message(data)

    async def thread_safe_get_received_messages(self):
        """Returns the received messages and clears the list"""
        if self.protocol is None:
            return
        await self.protocol.lock.acquire()
        self.received = self.protocol.received
        self.protocol.received = []
        self.protocol.lock.release()

    def get_received_messages(self):
        """Returns the received messages and clears the list"""
        self.loop.run_until_complete(self.thread_safe_get_received_messages())
        received = self.received
        self.received = []
        return received
