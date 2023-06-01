"""
Copyright (c) 2023, Miquel Massot
All rights reserved.
Licensed under the GPLv3 License.
See LICENSE.md file in the project root for full license information.
"""

from statemachine import State, StateMachine


class VoyisAPIStateMachine(StateMachine):
    idling = State("Idling", initial=True)
    connecting = State("Connecting")
    configuring = State("Configuring")
    readying = State("Ready")
    requesting_acquisition = State("Requesting acquisition")
    acquiring = State("Acquiring")
    requesting_stop = State("Requesting stop")
    stopping = State("Stopping")
    disconnecting = State("Disconnecting")

    connect = idling.to(connecting)
    configure = connecting.to(configuring)
    ready = configuring.to(readying)
    request_acquisition = readying.to(requesting_acquisition)
    acquire = requesting_acquisition.to(acquiring)
    request_stop = acquiring.to(requesting_stop)
    stop = requesting_stop.to(stopping)
    disconnect = stopping.to(disconnecting)
    reset = (
        connecting.to(idling)
        | configuring.to(idling)
        | readying.to(idling)
        | requesting_acquisition.to(idling)
        | acquiring.to(idling)
        | requesting_stop.to(idling)
        | stopping.to(idling)
        | disconnecting.to(idling)
    )

    def before_cycle(self, event: str, source: State, target: State, message: str = ""):
        message = ". " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"

    @property
    def requires_connection(self):
        return (
            self.current_state != self.idling
            and self.current_state != self.disconnecting
        )

    @property
    def is_idling(self):
        return self.current_state == self.idling

    @property
    def is_connecting(self):
        return self.current_state == self.connecting

    @property
    def is_configuring(self):
        return self.current_state == self.configuring

    @property
    def is_readying(self):
        return self.current_state == self.readying

    @property
    def is_requesting_acquisition(self):
        return self.current_state == self.requesting_acquisition

    @property
    def is_acquiring(self):
        return self.current_state == self.acquiring

    @property
    def is_requesting_stop(self):
        return self.current_state == self.requesting_stop

    @property
    def is_stopping(self):
        return self.current_state == self.stopping

    @property
    def is_disconnecting(self):
        return self.current_state == self.disconnecting
