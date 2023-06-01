"""
Copyright (c) 2023, Miquel Massot
All rights reserved.
Licensed under the GPLv3 License.
See LICENSE.md file in the project root for full license information.
"""

import asyncio
import logging
import threading
import time
from pathlib import Path

import nest_asyncio

from pyvoyis.api500 import API500Client
from pyvoyis.api500.defs import (
    API_PARAM_STILLS_IMAGE_SAVE_ORIGINAL,
    API_PARAM_STILLS_IMAGE_UNDISTORT,
    API_PARAM_STILLS_PROCESSED_IMAGE_FORMAT,
    ENDPOINT_ID_LOG,
    ENDPOINT_ID_SENSOR_LASER,
    ENDPOINT_ID_SENSOR_STILLS_PROCESSED,
    ENDPOINT_ID_SENSOR_STILLS_RAW,
    ENDPOINT_ID_STREAM,
    ENDPOINT_ID_XYZ_LASER,
    NAVPROTO_PSONNAV,
    SCANNER_CONNECTED_TO_THIS_API,
    SCANNER_PARAM_INDEX_OF_REFRACTION,
    SCANNER_PARAM_LASER_FREQ,
    SCANNER_PARAM_LASER_MAX_RANGE,
    SCANNER_PARAM_LASER_MIN_RANGE,
    SCANNER_PARAM_LASER_OUTPUT_GAIN,
    SCANNER_PARAM_LED_PANEL_INTENSITY,
    SCANNER_PARAM_MEMS_OUTPUT_ENABLE,
    SCANNER_PARAM_OUTPUT_LASER_DATA,
    SCANNER_PARAM_PROFILE_STILLS_EXP,
    SCANNER_PARAM_STILL_FREQ,
    SCANNER_PARAM_STILLS_IMAGE_LEVEL,
    SCANNER_STATUS_CONNECTED,
    SCANNER_STATUS_CPU_TEMP_CH,
    SCANNER_STATUS_CPU_TEMP_LASER,
    SCANNER_STATUS_CPU_TEMP_STILLS,
    SCANNER_STATUS_INTERNAL_TEMP_CH,
    SCANNER_STATUS_INTERNAL_TEMP_LASER_SENSOR,
    SCANNER_STATUS_INTERNAL_TEMP_STILLS_SENSOR,
    SCANNER_STATUS_LASER_CAMERA_CONNECTED,
    SCANNER_STATUS_LASER_CAMERA_READY,
    SCANNER_STATUS_LASER_CONNECTED,
    SCANNER_STATUS_LASER_DONGLE_AT_CH,
    SCANNER_STATUS_LASER_INHIBIT_ENABLED,
    SCANNER_STATUS_LASER_READY,
    SCANNER_STATUS_LASER_SAFETY_DISABLED,
    SCANNER_STATUS_LED_PANEL_CONNECTED,
    SCANNER_STATUS_LED_PANEL_READY,
    SCANNER_STATUS_READY,
    SCANNER_STATUS_SCAN_IN_PROGRESS,
    SCANNER_STATUS_SENSOR_TEMP_LASER_SENSOR,
    SCANNER_STATUS_SENSOR_TEMP_STILLS_SENSOR,
    SCANNER_STATUS_STILLS_CAMERA_CONNECTED,
    SCANNER_STATUS_STILLS_CAMERA_READY,
    SOURCE_TCP_CLIENT,
    SOURCE_TCP_SERVER,
    VALUE_TYPE_BOOL,
    VALUE_TYPE_UINT,
    scanner_connection_to_str,
)
from pyvoyis.commander import VoyisCommander
from pyvoyis.messages import (
    AckRsp,
    APIConfiguration,
    APIConfigurationNot,
    APIStatus,
    APIStatusNot,
    ApiVersionNot,
    ConnectionChangeNot,
    CorrectionModelListNot,
    CorrectionModelLoadNot,
    EndpointConfiguration,
    EndpointConfigurationNot,
    LeakDetectionNot,
    PendingCmdStatusNot,
    ScannerListNot,
    ScannerParameter,
    ScannerParametersNot,
    ScannerStatus,
    ScannerStatusNot,
)
from pyvoyis.state_machine import VoyisAPIStateMachine
from pyvoyis.tools.bool2str import bool2str
from pyvoyis.tools.rate import Rate
from pyvoyis.tools.safe_get import safe_get

nest_asyncio.apply()


class VoyisAPI:
    def __init__(self, config):
        """Class to handle the Voyis API"""
        self.config = config
        self.ip = config.ip_address
        self.port = config.port
        self.log = logging.getLogger("VoyisAPI")
        self.event = threading.Event()
        self.task_set = set()
        self.loop = asyncio.get_event_loop()
        self.client = API500Client(self.ip, self.port, self.loop, self.task_set)
        self.state = VoyisAPIStateMachine()
        self.cmd = VoyisCommander()

        self.api_status_not_dict = {}
        self.scanner_list_not_dict = {}
        self.scanner_parameters_not_dict = {}
        self.scanner_status_not_dict = {}
        self.api_configuration_not_dict = {}
        self.endpoint_configuration_not_dict = {}

        self.api_version_not_list = []
        self.api_status_list = []
        self.connection_change_not_list = []
        self.scanner_status_list = []
        self.leak_detection_not_list = []
        self.scanner_parameter_list = []
        self.api_configuration_list = []
        self.endpoint_configuration_list = []
        self.correction_model_load_not_list = []
        self.correction_model_list_not_list = []
        self.pending_cmd_status_not_list = []
        self.ack_rsp_list = []

        self._request_acquisition = False
        self._request_stop = False

    def request_acquisition(self):
        """Request acquisition"""
        self._request_acquisition = True

    def request_stop(self):
        """Request stop"""
        self._request_stop = True

    def send_message(self, cmd, timeout_s=6.0):
        """Sends a message to the API500Client

        Parameters
        ----------
        cmd : API500Command
            Command to send
        timeout_s : float, optional
            Timeout in seconds to wait for the AckRsp, by default 6.0

        Returns
        -------
        bool
            True if the command was accepted, False otherwise
        """
        len_ack_before = len(self.ack_rsp_list)
        self.loop.run_until_complete(self.client.send_message(cmd.to_str()))
        # Wait for AckRsp to be received
        timeout_start = time.time()
        while time.time() < timeout_start + timeout_s:
            if len(self.ack_rsp_list) == len_ack_before + 1:
                break
            time.sleep(0.1)
        if len(self.ack_rsp_list) > 0:
            ack_rsp = self.ack_rsp_list.pop()
            if not ack_rsp.accepted:
                self.log.error(
                    "Command {} not accepted: {}".format(
                        cmd.command, ack_rsp.nack_error_string
                    )
                )
            elif ack_rsp.accepted:
                self.log.info("Command {} accepted!".format(cmd.command))
            return ack_rsp.accepted
        else:
            return False

    def get_received_messages(self):
        """Get the received messages from the API500Client

        Returns
        -------
        list
            List of received messages
        """
        return self.client.get_received_messages()

    def shutdown(self):
        """Gracefully shutdown the API client"""
        self.log.info("Keyboard interrupt received, stopping...")
        if self.state.is_acquiring:
            self.stop_scanning()
        # Stop all threads
        if self.client.connected:
            self.stop_scanning_if_running()
            self.disconnect()

        # Stop the listen_api_thread
        self.event.set()
        self.listen_api_thread.join()

        for t in self.task_set:
            t.cancel()

        self.loop.stop()

        # Stop the asyncio_thread
        self.asyncio_thread.join()

    def infinite_loop(self):
        """Infinite loop to run the state machine"""
        # Check connection status
        if not self.client.connected and self.state.requires_connection:
            self.log.error("Connection lost. Resetting state machine...")
            self.state.reset()
            return

        if self.state.is_idling:
            self.state.connect()
        elif self.state.is_connecting:
            success = self.query_api_version()
            if not success:
                self.log.error("Could not query API version")
                return
            success = self.connect_to_scanner()
            if not success:
                self.log.error("Could not connect to scanner")
                return
            success = self.check_connection_status()
            if not success:
                self.log.error("Could not check connection status")
                return
            self.state.configure()
        elif self.state.is_configuring:
            success = self.set_data_options()
            if not success:
                self.log.error("Could not set data options")
                return
            # Necessary to be able to read armed / temperatures
            success = self.get_scanner_status()
            if not success:
                self.log.error("Could not get scanner status")
                return
            success = self.perform_system_checks()
            if not success:
                self.log.error("Could not perform system checks or some checks failed")
                return
            success = self.stop_scanning_if_running()
            if not success:
                self.log.error("Could not stop scanning")
            """
            success = self.configure_time_source()
            if not success:
                self.log.error('Could not configure time source')
                return
            """
            """
            success = self.configure_nav()
            if not success:
                self.log.error('Could not configure nav')
                return
            """
            success = self.set_scan_parameters()
            if not success:
                self.log.error("Could not set scan parameters")
                return
            success = self.check_laser_is_armed()
            if not success:
                self.log.error("Could not check laser is armed")
                return
            success = self.check_temperatures()
            if not success:
                self.log.error("Could not check temperatures")
                return
            self.state.ready()
        if self.state.is_readying and self._request_acquisition:
            self._request_acquisition = False
            self.state.request_acquisition()
        elif self.state.is_requesting_acquisition:
            success = self.start_scanning()
            if not success:
                self.log.error("Could not start scanning")
                return
            self.state.acquire()
        elif self.state.is_acquiring:
            success = self.get_scanner_status()
            if not success:
                self.log.error("Could not get scanner status")
                return
            if self._request_stop:
                self.state.request_stop()
        elif self.state.is_requesting_stop:
            success = self.stop_scanning()
            if not success:
                self.log.error("Could not stop scanning")
                return
            self.state.stop()
        elif self.state.is_stopping:
            self.state.disconnect()
        elif self.state.is_disconnecting:
            success = self.disconnect()
            if not success:
                self.log.error("Could not disconnect")
                return
            self.state.idle()

    def run(self):
        """Main function to run the API client"""
        self.asyncio_thread = threading.Thread(target=self.asyncio_thread_fn)
        self.asyncio_thread.start()

        # Prepare a background thread to listen to the API and keep it alive
        self.listen_api_thread = threading.Thread(target=self.listen_api_thread_fn)
        self.listen_api_thread.start()

        try:
            while not self.client.connected:
                time.sleep(1)
            while True:
                self.log.info("[State]: {}".format(self.state.current_state_value))
                self.infinite_loop()
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()

    def asyncio_thread_fn(self):
        """Thread to run the asyncio loop"""
        task = self.loop.create_task(self.client.connect())
        self.task_set.add(task)
        try:
            # run_forever() returns after calling loop.stop()
            self.loop.run_forever()
            for t in [t for t in self.task_set if not (t.done() or t.cancelled())]:
                # give canceled tasks the last chance to run
                self.loop.run_until_complete(t)
        finally:
            self.loop.close()
            self.log.info("Stopped")

    def listen_api_thread_fn(self):
        """Thread to listen to the API and process incomming messages"""
        rate = Rate(1)
        while True:
            received = self.get_received_messages()
            if len(received) > 0:
                for msg in received:
                    self.process_message(msg)
            rate.sleep()
            if self.event.is_set():
                break

    def connect_to_scanner(self):
        """Connect to scanner

        Returns
        -------
        bool
            True if the connection was successful, False otherwise
        """
        self.log.info("[VoyisAPI]: Connecting to scanner...")
        self.cmd.check_for_scanner.payload = {"ip_address": self.ip}
        success = self.send_message(self.cmd.check_for_scanner)

        if not success:
            return False

        if not self.is_scanner_connected():
            self.cmd.connect_scanner.payload = {"ip_address": self.ip}
            return self.send_message(self.cmd.connect_scanner)
        return True

    def check_connection_status(self):
        """Check connection status

        Returns
        -------
        bool
            True if the command was successful, False otherwise
        """
        self.log.info("[VoyisAPI]: check_connection_status")
        return self.send_message(self.cmd.query_scanner_status)

    def set_data_options(self):
        """Routine to configure endpoints

        Returns
        -------
        bool
            True if all commands were successful, False otherwise
        """
        self.log.info("[VoyisAPI]: Setting data options...")

        success = self.send_message(self.cmd.disable_nas)
        success = self.send_message(self.cmd.disable_local_storage)

        self.cmd.set_endpoints.payload = [
            {
                "endpoint_id": ENDPOINT_ID_LOG,
                "net_enabled": False,
                "net_connection": "",
                "file_enabled": True,
                "file_name": self.config.endpoind_id.log,
                "file_max_bytes": 1024 * 1024 * 1024,
            },
            {
                "endpoint_id": ENDPOINT_ID_STREAM,
                "net_enabled": False,
                "net_connection": "",
                "file_enabled": True,
                "file_name": self.config.endpoind_id.stream,
                "file_max_bytes": 1024 * 1024 * 1024,
            },
            {
                "endpoint_id": ENDPOINT_ID_XYZ_LASER,
                "net_enabled": False,
                "net_connection": "",
                "file_enabled": True,
                "file_name": self.config.endpoind_id.xyz_laser,
                "file_max_bytes": 1024 * 1024 * 1024,
            },
            {
                "endpoint_id": ENDPOINT_ID_SENSOR_LASER,
                "net_enabled": False,
                "net_connection": "",
                "file_enabled": True,
                "file_name": self.config.endpoind_id.sensor_laser,
                "file_max_bytes": 0,
            },
            {
                "endpoint_id": ENDPOINT_ID_SENSOR_STILLS_RAW,
                "net_enabled": False,
                "net_connection": "",
                "file_enabled": True,
                "file_name": self.config.endpoind_id.sensor_stills_raw,
                "file_max_bytes": 0,
            },
            {
                "endpoint_id": ENDPOINT_ID_SENSOR_STILLS_PROCESSED,
                "net_enabled": False,
                "net_connection": "",
                "file_enabled": True,
                "file_name": self.config.endpoind_id.sensor_stills_processed,
                "file_max_bytes": 0,
            },
        ]

        success = self.send_message(self.cmd.set_endpoints)
        if not success:
            return False

        # self.send_message(self.cmd.query_endpoint_configuration) does not work
        return success

    def is_scanner_connected(self):
        """Check if the scanner is connected to this API

        The system will notify the status of the scanner (available, connected, etc.)
        with ScannerListNot. The states 3 and 5 indicate ready and connected states
        respectively.

        Returns
        -------
        bool
            True if the scanner is connected to this API, False otherwise
        """
        self.send_message(self.cmd.list_scanners)

        self.cmd.check_for_scanner.payload = {"ip_address": self.ip}
        self.send_message(self.cmd.check_for_scanner)

        while len(self.scanner_list_not_dict) == 0:
            time.sleep(1)
            self.log.info("Waiting for ScannerListNot")
            if not self.client.connected:
                return False

        scanner_connection_state = safe_get(self.scanner_list_not_dict, self.ip)
        if scanner_connection_state is None:
            self.log.warning("Scanner not found in ScannerListNot")
            return False

        self.log.info("[VoyisAPI]: Scanner found in ScannerListNot")
        self.log.info(
            "[VoyisAPI]: Scanner connection state: {}".format(
                scanner_connection_to_str(scanner_connection_state)
            )
        )

        return scanner_connection_state == SCANNER_CONNECTED_TO_THIS_API

    def stop_scanning_if_running(self):
        """Helper function to stop scanning if it is running

        Returns
        -------
        bool
            True if the scanner was stopped, False otherwise
        """
        success = False
        if SCANNER_STATUS_SCAN_IN_PROGRESS not in self.scanner_status_not_dict:
            self.log.debug("Assumed scanner is not scanning...")
            return True

        while self.scanner_status_not_dict[SCANNER_STATUS_SCAN_IN_PROGRESS].value:
            self.log.info("Scan in progress, trying to stop it...")
            success = self.stop_scanning()
            if success:
                break
            time.sleep(5)
        return success

    def perform_system_checks(self):
        """Perform system checks

        Returns
        -------
        bool
            True if all checks were successful, False otherwise
        """
        self.log.info("[VoyisAPI]: Performing system checks...")
        # Check parameter notifications
        success = self.send_message(self.cmd.query_scanner_parameters)
        if not success:
            return False

        # Upon reception of this command, API will generate scanner status notification
        success = self.send_message(self.cmd.query_scanner_status)
        if not success:
            return False

        # Check current FPS
        """
        res = safe_get(
            self.scanner_status_not_dict, 
            SCANNER_STATUS_LASER_SENSOR_ACTUAL_FPS)
        if res is not None:
        self.log.info(
            "SCANNER_STATUS_LASER_SENSOR_ACTUAL_FPS: {}".format(res.value.get()))
        res = safe_get(
            self.scanner_status_not_dict, 
            SCANNER_STATUS_STILLS_SENSOR_ACTUAL_FPS)
        if res is not None:
        self.log.info(
            "SCANNER_STATUS_STILLS_SENSOR_ACTUAL_FPS: {}".format(res.value.get()))
        """

        api_connected = safe_get(self.scanner_status_not_dict, SCANNER_STATUS_CONNECTED)
        api_ready = safe_get(self.scanner_status_not_dict, SCANNER_STATUS_READY)

        stills_cam_connected = safe_get(
            self.scanner_status_not_dict, SCANNER_STATUS_STILLS_CAMERA_CONNECTED
        )
        stills_cam_ready = safe_get(
            self.scanner_status_not_dict, SCANNER_STATUS_STILLS_CAMERA_READY
        )

        laser_cam_connected = safe_get(
            self.scanner_status_not_dict, SCANNER_STATUS_LASER_CAMERA_CONNECTED
        )
        laser_cam_ready = safe_get(
            self.scanner_status_not_dict, SCANNER_STATUS_LASER_CAMERA_READY
        )

        laser_connected = safe_get(
            self.scanner_status_not_dict, SCANNER_STATUS_LASER_CONNECTED
        )
        laser_ready = safe_get(self.scanner_status_not_dict, SCANNER_STATUS_LASER_READY)

        led_panel_connected = safe_get(
            self.scanner_status_not_dict, SCANNER_STATUS_LED_PANEL_CONNECTED
        )
        led_panel_ready = safe_get(
            self.scanner_status_not_dict, SCANNER_STATUS_LED_PANEL_READY
        )

        self.log.info("[VoyisAPI]: Device status:")
        self.log.info(
            "  * API: {} {}".format(
                "Connected" if api_connected else "NOT Connected",
                "Ready" if api_ready else "NOT Ready",
            )
        )
        self.log.info(
            "  * Stills camera: {} {}".format(
                "Connected" if stills_cam_connected else "NOT Connected",
                "Ready" if stills_cam_ready else "NOT Ready",
            )
        )
        self.log.info(
            "  * Laser camera: {} {}".format(
                "Connected" if laser_cam_connected else "NOT Connected",
                "Ready" if laser_cam_ready else "NOT Ready",
            )
        )
        self.log.info(
            "  * Laser: {} {}".format(
                "Connected" if laser_connected else "NOT Connected",
                "Ready" if laser_ready else "NOT Ready",
            )
        )
        self.log.info(
            "  * LED panel: {} {}".format(
                "Connected" if led_panel_connected else "NOT Connected",
                "Ready" if led_panel_ready else "NOT Ready",
            )
        )

        """
        return (
            api_ready
            and stills_cam_ready
            and laser_cam_ready
            and laser_ready
            and led_panel_ready
        )
        """
        return True

    def configure_time_source(self):
        """Sends command to configure time source

        Returns
        -------
        bool
            True if the command was successful, False otherwise
        """
        self.log.info("[VoyisAPI]: Configuring time source...")

        self.cmd.set_time_tag_source.payload = {
            "network": SOURCE_TCP_CLIENT,
            "connection": "4010",
        }

        return self.send_message(self.cmd.set_time_tag_source)

    def configure_nav(self):
        """Sends command to configure the navigation source

        Returns
        -------
        bool
            True if the command was successful, False otherwise
        """
        self.log.info("[VoyisAPI]: Configuring nav...")

        self.cmd.set_nav_data_source.payload = {
            "network": SOURCE_TCP_SERVER,
            "protocol": NAVPROTO_PSONNAV,
            "connection": "192.168.179.10:4003",
        }
        return self.send_message(self.cmd.set_nav_data_source)

    def set_scan_parameters(self):
        """Sets the scan parameters

        Returns
        -------
        bool
            True if the command was successful, False otherwise
        """
        self.log.info("[VoyisAPI]: Setting scan parameters...")
        cfg = self.config.scanner_param.s
        self.cmd.set_local_scanner_parameters.payload = [
            {
                "parameter_id": SCANNER_PARAM_PROFILE_STILLS_EXP,
                "value": str(cfg.scanner_param.stills_exp_us),
                "type": VALUE_TYPE_UINT,
            },
            {
                "parameter_id": SCANNER_PARAM_LASER_FREQ,
                "value": str(int(cfg.scanner_param.laser_freq_hz * 1000)),
                "type": VALUE_TYPE_UINT,
            },
            {
                "parameter_id": SCANNER_PARAM_STILL_FREQ,
                "value": str(int(cfg.scanner_param.stills_freq_hz * 1000)),
                "type": VALUE_TYPE_UINT,
            },
            {  # If true, laser freq is 1 Hz
                "parameter_id": SCANNER_PARAM_OUTPUT_LASER_DATA,
                "value": bool2str(cfg.save_laser_images),
                "type": VALUE_TYPE_BOOL,
            },
            {
                "parameter_id": SCANNER_PARAM_MEMS_OUTPUT_ENABLE,
                "value": "false",
                "type": VALUE_TYPE_BOOL,
            },
            {
                "parameter_id": SCANNER_PARAM_LASER_MIN_RANGE,
                "value": str(cfg.laser_min_range_cm),
                "type": VALUE_TYPE_UINT,
            },
            {
                "parameter_id": SCANNER_PARAM_LASER_MAX_RANGE,
                "value": str(cfg.laser_max_range_cm),
                "type": VALUE_TYPE_UINT,
            },
            {
                "parameter_id": SCANNER_PARAM_INDEX_OF_REFRACTION,
                "value": str(int(cfg.index_of_refraction * 1e6)),
                "type": VALUE_TYPE_UINT,
            },
            {
                "parameter_id": SCANNER_PARAM_LED_PANEL_INTENSITY,
                "value": str(cfg.led_panel_intensity_percentage),
                "type": VALUE_TYPE_UINT,
            },
            {
                "parameter_id": SCANNER_PARAM_LASER_OUTPUT_GAIN,
                "value": str(cfg.laser_gain_percentage),
                "type": VALUE_TYPE_UINT,
            },
            {
                "parameter_id": SCANNER_PARAM_STILLS_IMAGE_LEVEL,
                "value": str(cfg.stills_image_level),
                "type": VALUE_TYPE_UINT,
            },
        ]

        success = self.send_message(self.cmd.set_local_scanner_parameters)
        if not success:
            return False

        success = self.send_message(self.cmd.apply_local_scanner_parameters)
        if not success:
            return False

        self.cmd.set_api_configuration.payload = [
            {
                "parameter_id": API_PARAM_STILLS_IMAGE_UNDISTORT,
                "value": bool2str(cfg.undistort_images, "1", "0"),
                "type": VALUE_TYPE_UINT,
            },
            {
                "parameter_id": API_PARAM_STILLS_IMAGE_SAVE_ORIGINAL,
                "value": bool2str(cfg.save_original, "1", "0"),
                "type": VALUE_TYPE_BOOL,
            },
            {
                "parameter_id": API_PARAM_STILLS_PROCESSED_IMAGE_FORMAT,
                "value": bool2str(cfg.processed_image_format, "1", "0"),
                "type": VALUE_TYPE_UINT,
            },
        ]
        return self.send_message(self.cmd.set_api_configuration)

    def check_laser_is_armed(self):
        """Helper function to check if the laser is armed

        Returns
        -------
        bool
            True if the laser is armed, False otherwise
        """
        self.log.info("[VoyisAPI]: Checking laser is armed...")

        # Check laser safety / inhibit
        res = safe_get(self.scanner_status_not_dict, SCANNER_STATUS_LASER_CONNECTED)
        if res is not None:
            self.log.info("[VoyisAPI]: Laser connected? {}".format(res.value.get()))

        res = safe_get(self.scanner_status_not_dict, SCANNER_STATUS_LASER_READY)
        if res is not None:
            self.log.info("[VoyisAPI]: Laser ready? {}".format(res.value.get()))

        res = safe_get(self.scanner_status_not_dict, SCANNER_STATUS_LASER_DONGLE_AT_CH)
        if res is not None:
            self.log.info(
                "[VoyisAPI]: Laser dongle connected? {}".format(res.value.get())
            )

        res = safe_get(
            self.scanner_status_not_dict, SCANNER_STATUS_LASER_INHIBIT_ENABLED
        )
        if res is not None:
            self.log.info("[VoyisAPI]: Laser inhibited? {}".format(res.value.get()))
        res = safe_get(
            self.scanner_status_not_dict, SCANNER_STATUS_LASER_SAFETY_DISABLED
        )
        if res is not None:
            if res.value:
                self.log.info("[VoyisAPI]: Laser key: DISARM")
            else:
                self.log.info("[VoyisAPI]: Laser key: ARMED")
        return True

    def check_temperatures(self):
        """Helper function to check temperatures

        Returns
        -------
        bool
            True if all checks were successful, False otherwise
        """
        self.log.info("[VoyisAPI]: Checking temperatures")
        # Check temperatures
        cpu_temp_ch = safe_get(self.scanner_status_not_dict, SCANNER_STATUS_CPU_TEMP_CH)
        internal_temp_ch = safe_get(
            self.scanner_status_not_dict, SCANNER_STATUS_INTERNAL_TEMP_CH
        )
        sensor_temp_laser_sensor = safe_get(
            self.scanner_status_not_dict, SCANNER_STATUS_SENSOR_TEMP_LASER_SENSOR
        )
        cpu_temp_laser = safe_get(
            self.scanner_status_not_dict, SCANNER_STATUS_CPU_TEMP_LASER
        )
        internal_temp_laser_sensor = safe_get(
            self.scanner_status_not_dict, SCANNER_STATUS_INTERNAL_TEMP_LASER_SENSOR
        )
        sensor_temp_stills_sensor = safe_get(
            self.scanner_status_not_dict, SCANNER_STATUS_SENSOR_TEMP_STILLS_SENSOR
        )
        cpu_temp_stills = safe_get(
            self.scanner_status_not_dict, SCANNER_STATUS_CPU_TEMP_STILLS
        )
        internal_temp_stills_sensor = safe_get(
            self.scanner_status_not_dict, SCANNER_STATUS_INTERNAL_TEMP_STILLS_SENSOR
        )

        self.log.info("Temperature readings:")
        if cpu_temp_ch is not None:
            self.log.info("  * cpu_temp_ch: {} C".format(cpu_temp_ch.value.get()))
        if internal_temp_ch is not None:
            self.log.info(
                "  * internal_temp_ch: {} C".format(internal_temp_ch.value.get())
            )
        if sensor_temp_laser_sensor is not None:
            self.log.info(
                "  * sensor_temp_laser_sensor: {} C".format(
                    sensor_temp_laser_sensor.value.get()
                )
            )
        if cpu_temp_laser is not None:
            self.log.info("  * cpu_temp_laser: {} C".format(cpu_temp_laser.value.get()))
        if internal_temp_laser_sensor is not None:
            self.log.info(
                "  * internal_temp_laser_sensor: {} C".format(
                    internal_temp_laser_sensor.value.get()
                )
            )
        if sensor_temp_stills_sensor is not None:
            self.log.info(
                "  * sensor_temp_stills_sensor: {} C".format(
                    sensor_temp_stills_sensor.value.get()
                )
            )
        if cpu_temp_stills is not None:
            self.log.info(
                "  * cpu_temp_stills: {} C".format(cpu_temp_stills.value.get())
            )
        if internal_temp_stills_sensor is not None:
            self.log.info(
                "  * internal_temp_stills_sensor: {} C".format(
                    internal_temp_stills_sensor.value.get()
                )
            )
        if internal_temp_ch is not None:
            return internal_temp_ch.value.get() < 60
        else:
            return True

    def start_scanning(self):
        """Sends the command to start scanning

        Returns
        -------
        bool
            True if the command was successful, False otherwise
        """
        self.log.info("[VoyisAPI]: Start scanning...")
        # Set mode to profiling
        self.cmd.start_scanner.payload = {"mode": 0}
        return self.send_message(self.cmd.start_scanner)

    def stop_scanning(self):
        """Sends the command to stop scanning

        Returns
        -------
        bool
            True if the command was successful, False otherwise
        """
        self.log.info("[VoyisAPI]: Stop scanning...")
        success = self.send_message(self.cmd.stop_scanner)
        return success

    def get_scanner_status(self):
        """Sends the command to query the scanner status

        Returns
        -------
        bool
            True if the command was successful, False otherwise
        """
        self.log.info("[VoyisAPI]: Querying scanner status...")
        return self.send_message(self.cmd.query_scanner_status)

    def ping_api(self):
        """Sends the command to ping the API

        Returns
        -------
        bool
            True if the command was successful, False otherwise
        """
        return self.send_message(self.cmd.ping_api)

    def query_api_version(self):
        """Sends the command to query the API version

        Returns
        -------
        bool
            True if the command was successful, False otherwise
        """
        return self.send_message(self.cmd.query_api_version)

    def disconnect(self):
        """Sends the command to disconnect from the scanner

        Returns
        -------
        bool
            True if the command was successful, False otherwise
        """
        return self.send_message(self.cmd.disconnect)

    def process_message(self, data):
        """Routine to process incomming messages

        Parameters
        ----------
        data : dict
            Message data
        """
        # Handle logging
        logging_file = Path(logging.getLoggerClass().root.handlers[0].baseFilename)
        date_str = "_".join(logging_file.stem.split("_")[0:2])

        message = data["message"]
        if message == "ApiVersionNot":
            msg_class = ApiVersionNot(data)
            self.api_version_not_list.append(msg_class)
        elif message == "APIStatus":
            msg_class = APIStatus(data)
            self.api_status_list.append(msg_class)
        elif message == "APIStatusNot":
            msg_class = APIStatusNot(data)
            for asn in msg_class.statuses:
                if asn.status_id in self.api_status_not_dict:
                    self.api_status_not_dict[asn.status_id].update(asn)
                else:
                    self.api_status_not_dict[asn.status_id] = asn
            # Save dict as json
            api_status_not_file = logging_file.parent / (
                date_str + "_api_status_not.yaml"
            )
            if api_status_not_file.exists():
                # delete the file
                api_status_not_file.unlink()
            with api_status_not_file.open("a", encoding="utf-8") as f:
                for key in self.api_status_not_dict:
                    val = self.api_status_not_dict[key]
                    f.write(val.to_yaml())
        elif message == "ScannerListNot":
            msg_class = ScannerListNot(data)
            for idx in range(msg_class.size()):
                self.scanner_list_not_dict[
                    msg_class.ip_addresses[idx]
                ] = msg_class.connection_states[idx]
        elif message == "ConnectionChangeNot":
            msg_class = ConnectionChangeNot(data)
            self.connection_change_not_list.append(msg_class)
        elif message == "ScannerStatus":
            msg_class = ScannerStatus(data)
            self.scanner_status_list.append(msg_class)
        elif message == "ScannerStatusNot":
            msg_class = ScannerStatusNot(data)
            for ssnot in msg_class.statuses:
                if ssnot.status_id in self.scanner_status_not_dict:
                    self.scanner_status_not_dict[ssnot.status_id].update(ssnot)
                else:
                    self.scanner_status_not_dict[ssnot.status_id] = ssnot
            # Save dict as json
            scanner_status_not_file = logging_file.parent / (
                date_str + "_scanner_status_not.yaml"
            )
            if scanner_status_not_file.exists():
                # delete the file
                scanner_status_not_file.unlink()
            with scanner_status_not_file.open("a", encoding="utf-8") as f:
                for key in self.scanner_status_not_dict:
                    val = self.scanner_status_not_dict[key]
                    f.write(val.to_yaml())
        elif message == "LeakDetectionNot":
            msg_class = LeakDetectionNot(data)
            self.leak_detection_not_list.append(msg_class)
        elif message == "ScannerParameter":
            msg_class = ScannerParameter(data)
            self.scanner_parameter_list.append(msg_class)
        elif message == "ScannerParametersNot":
            msg_class = ScannerParametersNot(data)
            for spnot in msg_class.parameters:
                if spnot.parameter_id in self.scanner_parameters_not_dict:
                    self.scanner_parameters_not_dict[spnot.parameter_id].update(spnot)
                else:
                    self.scanner_parameters_not_dict[spnot.parameter_id] = spnot
            # Save dict as json
            scanner_parameters_not_file = logging_file.parent / (
                date_str + "_scanner_parameters_not.yaml"
            )
            if scanner_parameters_not_file.exists():
                # delete the file
                scanner_parameters_not_file.unlink()
            with scanner_parameters_not_file.open("a", encoding="utf-8") as f:
                for key in self.scanner_parameters_not_dict:
                    val = self.scanner_parameters_not_dict[key]
                    f.write(val.to_yaml())

        elif message == "APIConfiguration":
            msg_class = APIConfiguration(data)
            self.api_configuration_list.append(msg_class)
        elif message == "APIConfigurationNot":
            msg_class = APIConfigurationNot(data)
            for acnot in msg_class.api_configurations:
                self.api_configuration_not_dict[acnot.parameter_id] = acnot
            # Save dict as json
            logging_file = Path(logging.getLoggerClass().root.handlers[0].baseFilename)
            api_configuration_not_file = logging_file.parent / (
                date_str + "_api_configuration_not.yaml"
            )
            if api_configuration_not_file.exists():
                # delete the file
                api_configuration_not_file.unlink()
            with api_configuration_not_file.open("a", encoding="utf-8") as f:
                for key in self.api_configuration_not_dict:
                    val = self.api_configuration_not_dict[key]
                    f.write(val.to_yaml())
        elif message == "EndpointConfiguration":
            msg_class = EndpointConfiguration(data)
            self.endpoint_configuration_list.append(msg_class)
        elif message == "EndpointConfigurationNot":
            msg_class = EndpointConfigurationNot(data)
            for ecnot in msg_class.endpoint_configurations:
                self.endpoint_configuration_not_dict[ecnot.endpoint_id] = ecnot
            # Save dict as json
            endpoint_configuration_not_file = logging_file.parent / (
                date_str + "_endpoint_configuration_not.yaml"
            )
            if endpoint_configuration_not_file.exists():
                # delete the file
                endpoint_configuration_not_file.unlink()
            with endpoint_configuration_not_file.open("a", encoding="utf-8") as f:
                for key in self.endpoint_configuration_not_dict:
                    val = self.endpoint_configuration_not_dict[key]
                    f.write(val.to_yaml())
        elif message == "CorrectionModelLoadNot":
            msg_class = CorrectionModelLoadNot(data)
            self.correction_model_load_not_list.append(msg_class)
        elif message == "CorrectionModelListNot":
            msg_class = CorrectionModelListNot(data)
            self.correction_model_list_not_list.append(msg_class)
        elif message == "PendingCmdStatusNot":
            msg_class = PendingCmdStatusNot(data)
            self.pending_cmd_status_not_list.append(msg_class)
        elif message == "AckRsp":
            msg_class = AckRsp(data)
            self.ack_rsp_list.append(msg_class)
