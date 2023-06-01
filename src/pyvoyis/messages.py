"""
Copyright (c) 2023, Miquel Massot
All rights reserved.
Licensed under the GPLv3 License.
See LICENSE.md file in the project root for full license information.
"""

import datetime
import json

from pyvoyis.api500.defs import (
    api_param_stills_to_str,
    api_status_to_str,
    endpoint_id_to_str,
    scanner_param_to_str,
    scanner_status_to_str,
)


class ValueHistory:
    def __init__(self, value=None):
        """Class to record a history of values and times."""
        self.values = []
        self.times = []
        if value is not None:
            # Get current time in epoch
            time = datetime.datetime.now().timestamp()
            self.values.append(value)
            self.times.append(time)

    def add(self, value):
        self.values.append(value)
        self.times.append(datetime.datetime.now().timestamp())

    def get(self, index=-1, return_time=False):
        if return_time:
            return self.values[index], self.times[index]
        else:
            return self.values[index]

    def size(self):
        return len(self.values)

    def __str__(self):
        msg = "\n        values: {}, ".format(self.values)
        msg += "\n        times: {}".format(self.times)
        return msg


class API500Message:
    def __init__(self, data=None, message=None, payload=None):
        """Class to store JSON messages from Voyis API in the form of a dictionary.

        Example:
        {
          "message": "SetLocalScannerParametersCmd",
          "payload": [
            {
              "parameter_id": 0,
              "value": "false",
              "type": 0
            },
            {
              "parameter_id": 15,
              "value": "150",
              "type": 3
            }
          ]
        }
        """
        self.message = ""
        self.payload = None

        if message is not None:
            self.message = message
        if payload is not None:
            self.payload = payload

        if data is None:
            return
        self.message = data["message"]
        if "payload" in data:
            self.payload = data["payload"]
        if "message" not in data:
            raise ValueError("Message not in data")

    def to_str(self):
        if self.payload is None:
            dict_msg = {
                "message": self.message,
            }
        else:
            dict_msg = {"message": self.message, "payload": self.payload}
        return json.dumps(dict_msg)

    def __str__(self):
        return self.to_json()

    def __repr__(self):
        return self.__str__()


class ApiVersionNot(API500Message):
    def __init__(self, data=None):
        super().__init__(data)
        self.version = self.payload["version"]
        self.date = self.payload["date"]

    def __str__(self):
        return "ApiVersionNot: {} ({})".format(self.version, self.date)


class APIStatus:
    def __init__(self, json_dict):
        self.status_id = json_dict["status_id"]
        self.name = json_dict["name"]
        self.value_type = json_dict["value_type"]
        self.value = ValueHistory(json_dict["value"])

    def update(self, other):
        self.value.add(other.value.get())

    def __str__(self):
        msg = "APIStatus: {} ({}) = {}".format(
            self.name, self.status_id, self.value.get()
        )
        return msg

    def to_yaml(self):
        msg = api_status_to_str(self.status_id) + ":"
        msg += "\n    status_id: " + str(self.status_id)
        msg += "\n    name: " + str(self.name)
        msg += "\n    value_type: " + str(self.value_type)
        msg += "\n    value: " + str(self.value)
        msg += "\n"
        return msg


class APIStatusNot(API500Message):
    def __init__(self, data=None):
        super().__init__(data)
        self.statuses = []
        for p in self.payload:
            self.statuses.append(APIStatus(p))

    def __str__(self):
        return "APIStatusNot: {}".format(self.statuses)


class ScannerListNot(API500Message):
    def __init__(self, data=None):
        super().__init__(data)
        self.ip_addresses = []
        self.connection_states = []

        for p in self.payload:
            ip_address = p["ip_address"]
            connection_state = p["connection_state"]
            self.ip_addresses.append(ip_address)
            self.connection_states.append(connection_state)

    def size(self):
        return len(self.ip_addresses)

    def __str__(self):
        return "ScannerListNot: {}".format(self.ip_addresses)


class ConnectionChangeNot(API500Message):
    def __init__(self, data=None):
        super().__init__(data)
        self.connection_state = self.payload["connection_state"]

    def __str__(self):
        return "ConnectionChangeNot: {}".format(self.connection_state)


class ScannerStatus:
    def __init__(self, json_dict):
        self.status_id = json_dict["status_id"]
        self.name = json_dict["name"]
        self.value_type = json_dict["value_type"]
        self.value = ValueHistory(json_dict["value"])
        self.status_status = ValueHistory(json_dict["status_status"])
        self.category_id = json_dict["category_id"]
        self.category_name = json_dict["category_name"]

    def update(self, other):
        self.value.add(other.value.get())
        self.status_status.add(other.status_status.get())

    def __str__(self) -> str:
        msg = "ScannerStatus: "
        msg += " status_id: {}, ".format(self.status_id)
        msg += " name: {}, ".format(self.name)
        msg += " value_type: {}, ".format(self.value_type)
        msg += " value: {}, ".format(self.value)
        msg += " status_status: {}, ".format(self.status_status)
        msg += " category_id: {}, ".format(self.category_id)
        msg += " category_name: {}, ".format(self.category_name)
        return msg

    def to_yaml(self):
        msg = scanner_status_to_str(self.status_id) + ":"
        msg += "\n    status_id: " + str(self.status_id)
        msg += "\n    name: " + str(self.name)
        msg += "\n    value_type: " + str(self.value_type)
        msg += "\n    value: " + str(self.value)
        msg += "\n    status_status: " + str(self.status_status)
        msg += "\n    category_id: " + str(self.category_id)
        msg += "\n    category_name: " + str(self.category_name)
        msg += "\n"
        return msg


class ScannerStatusNot(API500Message):
    def __init__(self, data=None):
        super().__init__(data)
        self.statuses = []
        for p in self.payload:
            self.statuses.append(ScannerStatus(p))

    def get(self, status_id):
        for s in self.statuses:
            if s.status_id == status_id:
                return s
        return None

    def __str__(self):
        return "ScannerStatusNot: {}".format(self.statuses)


class LeakDetectionNot(API500Message):
    def __init__(self, data=None):
        super().__init__(data)
        self.leak_detected = self.payload["ch_leak_count"] > 0
        self.ch_leak_count = self.payload["ch_leak_count"]

    def __str__(self):
        return "LeakDetectionNot: {}".format(self.leak_detected)


class ScannerParameter:
    def __init__(self, json_dict):
        self.parameter_id = json_dict["parameter_id"]
        self.name = json_dict["name"]
        self.value_type = json_dict["value_type"]
        self.remote_value = ValueHistory(json_dict["remote_value"])
        self.local_value = ValueHistory(json_dict["local_value"])
        self.valid_min = json_dict["valid_min"]
        self.valid_max = json_dict["valid_max"]
        self.valid_step = json_dict["valid_step"]
        self.category_id = json_dict["category_id"]
        self.category_name = json_dict["category_name"]
        self.can_set_when_scanning = json_dict["can_set_when_scanning"]

    def update(self, other):
        self.remote_value.add(other.remote_value.get())
        self.local_value.add(other.local_value.get())

    def __str__(self):
        msg = "ScannerParameter: "
        msg += " parameter_id: {}, ".format(self.parameter_id)
        msg += " name: {}, ".format(self.name)
        msg += " value_type: {}, ".format(self.value_type)
        msg += " remote_value: {}, ".format(self.remote_value)
        msg += " local_value: {}, ".format(self.local_value)
        msg += " valid_min: {}, ".format(self.valid_min)
        msg += " valid_max: {}, ".format(self.valid_max)
        msg += " valid_step: {}, ".format(self.valid_step)
        msg += " category_id: {}, ".format(self.category_id)
        msg += " category_name: {}, ".format(self.category_name)
        msg += " can_set_when_scanning: {}, ".format(self.can_set_when_scanning)
        return msg

    def to_yaml(self):
        msg = scanner_param_to_str(self.parameter_id) + ":"
        msg += "\n    parameter_id: " + str(self.parameter_id)
        msg += "\n    name: " + str(self.name)
        msg += "\n    value_type: " + str(self.value_type)
        msg += "\n    remote_value: " + str(self.remote_value)
        msg += "\n    local_value: " + str(self.local_value)
        msg += "\n    valid_min: " + str(self.valid_min)
        msg += "\n    valid_max: " + str(self.valid_max)
        msg += "\n    valid_step: " + str(self.valid_step)
        msg += "\n    category_id: " + str(self.category_id)
        msg += "\n    category_name: " + str(self.category_name)
        msg += "\n    can_set_when_scanning: " + str(self.can_set_when_scanning)
        msg += "\n"
        return msg


class ScannerParametersNot(API500Message):
    def __init__(self, data=None):
        super().__init__(data)
        self.parameters = []
        for p in self.payload:
            self.parameters.append(ScannerParameter(p))

    def __str__(self):
        return "ScannerParametersNot: {}".format(self.parameters)


class APIConfiguration:
    def __init__(self, json_dict):
        self.parameter_id = json_dict["parameter_id"]
        self.name = json_dict["name"]
        self.value_type = json_dict["value_type"]
        self.value = ValueHistory(json_dict["value"])
        self.valid_min = json_dict["valid_min"]
        self.valid_max = json_dict["valid_max"]
        self.valid_step = json_dict["valid_step"]

    def update(self, other):
        self.value.add(other.value.get())

    def __str__(self):
        msg = "APIConfiguration: "
        msg += " parameter_id: {}, ".format(self.parameter_id)
        msg += " name: {}, ".format(self.name)
        msg += " value_type: {}, ".format(self.value_type)
        msg += " value: {}, ".format(self.value)
        msg += " valid_min: {}, ".format(self.valid_min)
        msg += " valid_max: {}, ".format(self.valid_max)
        msg += " valid_step: {}".format(self.valid_step)
        return msg

    def to_yaml(self):
        msg = api_param_stills_to_str(self.parameter_id) + ":"
        msg += "\n    parameter_id: " + str(self.parameter_id)
        msg += "\n    name: " + str(self.name)
        msg += "\n    value_type: " + str(self.value_type)
        msg += "\n    value: " + str(self.value)
        msg += "\n    valid_min: " + str(self.valid_min)
        msg += "\n    valid_max: " + str(self.valid_max)
        msg += "\n    valid_step: " + str(self.valid_step)
        msg += "\n"
        return msg


class APIConfigurationNot(API500Message):
    def __init__(self, data=None):
        super().__init__(data)
        self.api_configurations = []
        for p in self.payload:
            self.api_configurations.append(APIConfiguration(p))

    def __str__(self):
        return "APIConfigurationNot: {}".format(self.api_configurations)


class EndpointConfiguration:
    def __init__(self, json_dict):
        self.endpoint_id = json_dict["endpoint_id"]
        self.net_enabled = json_dict["net_enabled"]
        self.net_connection = json_dict["net_connection"]
        self.file_enabled = json_dict["file_enabled"]
        self.file_name = json_dict["file_name"]
        self.file_max_bytes = json_dict["file_max_bytes"]

    def __str__(self) -> str:
        msg = "EndpointConfiguration: "
        msg += " endpoint_id: {}, ".format(self.endpoint_id)
        msg += " net_enabled: {}, ".format(self.net_enabled)
        msg += " net_connection: {}, ".format(self.net_connection)
        msg += " file_enabled: {}, ".format(self.file_enabled)
        msg += " file_name: {}, ".format(self.file_name)
        msg += " file_max_bytes: {}".format(self.file_max_bytes)
        return msg

    def to_yaml(self):
        msg = endpoint_id_to_str(self.endpoint_id) + ":"
        msg += "\n    endpoint_id: " + str(self.endpoint_id)
        msg += "\n    net_enabled: " + str(self.net_enabled)
        msg += "\n    net_connection: " + str(self.net_connection)
        msg += "\n    file_enabled: " + str(self.file_enabled)
        msg += "\n    file_name: " + str(self.file_name)
        msg += "\n    file_max_bytes: " + str(self.file_max_bytes)
        msg += "\n"
        return msg


class EndpointConfigurationNot(API500Message):
    def __init__(self, data=None):
        super().__init__(data)
        self.endpoint_configurations = []
        for p in self.payload:
            self.endpoint_configurations.append(EndpointConfiguration(p))

    def __str__(self):
        return "EndpointConfigurationNot: {}".format(self.endpoint_configurations)


class CorrectionModelLoadNot(API500Message):
    def __init__(self, data=None):
        super().__init__(data)
        self.accepted = self.payload["accepted"]
        self.model_name = self.payload["model_name"]
        self.error = self.payload["error"]

    def __str__(self):
        msg = "CorrectionModelLoadNot: "
        msg += " accepted: {}, ".format(self.accepted)
        msg += " model_name: {}, ".format(self.model_name)
        msg += " error: {}".format(self.error)
        return msg


class CorrectionModelListNot(API500Message):
    def __init__(self, data=None):
        super().__init__(data)
        self.model_limit = self.payload["model_limit"]
        self.current_model = self.payload["current_model"]
        self.model_list = self.payload["model_list"]

    def __str__(self):
        msg = "CorrectionModelListNot: "
        msg += " model_limit: {}, ".format(self.model_limit)
        msg += " current_model: {}, ".format(self.current_model)
        msg += " model_list: {}".format(self.model_list)
        return msg


class PendingCmdStatusNot(API500Message):
    def __init__(self, data=None):
        super().__init__(data)
        self.completeness = self.payload["completeness"]
        self.time_remaining = self.payload["time_remaining"]
        self.command_id = self.payload["command_id"]

    def __str__(self):
        msg = "PendingCmdStatusNot: "
        msg += " completeness: {}, ".format(self.completeness)
        msg += " time_remaining: {}, ".format(self.time_remaining)
        msg += " command_id: {}".format(self.command_id)
        return msg


class AckRsp(API500Message):
    def __init__(self, data=None):
        super().__init__(data)
        self.accepted = self.payload["accepted"]
        self.command_id = self.payload["command_id"]
        self.nack_error_code = self.payload["nack_error_code"]
        self.nack_error_string = self.payload["nack_error_string"]
        self.api_version = self.payload["api_version"]

    def __str__(self):
        msg = "AckRsp: "
        msg += " accepted: {}, ".format(self.accepted)
        msg += " command_id: {}, ".format(self.command_id)
        msg += " nack_error_code: {}, ".format(self.nack_error_code)
        msg += " nack_error_string: {}, ".format(self.nack_error_string)
        msg += " api_version: {}".format(self.api_version)
        return msg
