"""
Copyright (c) 2023, Miquel Massot
All rights reserved.
Licensed under the GPLv3 License.
See LICENSE.md file in the project root for full license information.
"""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, validator


class ScannerParamConfig(BaseModel):
    stills_exp_us: int = 5000
    laser_exp_us: int = 1000
    laser_freq_hz: float = 30.0
    stills_freq_hz: float = 0.5
    save_laser_images: bool = False
    laser_min_range_cm: int = 150
    laser_max_range_cm: int = 2000
    index_of_refraction: float = 1.3
    led_panel_intensity_percentage: int = 100
    laser_gain_percentage: int = 100
    stills_image_level: int = 2
    stills_advanced_colour_mode: int = 0
    stills_advanced_colour_enhancement_lvl: int = 1
    stills_advanced_contrast_mode: int = 0
    stills_advanced_contrast_lvl: int = 0
    stills_advanced_brightness: float = 0.4
    stills_advanced_contrast: float = 0.15
    stills_advanced_white_balance: int = 0
    stills_advanced_adaptive_lighting: int = 0
    stills_undistort: bool = False
    stills_save_original: bool = False
    stills_processed_image_format: str = "jpg"
    laser_disable_range_gating: bool = False

    @validator("stills_processed_image_format")
    def valid_stills_processed_image_format(cls, v):
        if v not in ["jpg", "tiff", "tif", "jpeg"]:
            raise ValueError('stills_processed_image_format must be "jpg" or "tiff"')
        return v

    @property
    def stills_processed_image_format_uint(self):
        if self.stills_processed_image_format in ["tiff", "tif"]:
            return 0
        elif self.stills_processed_image_format in ["jpeg", "jpg"]:
            return 1

    @validator("stills_exp_us")
    def valid_stills_exp_us(cls, v):
        if v < 500:
            raise ValueError("stills_exp_us must be >= 500")
        elif v > 1000000:
            raise ValueError("stills_exp_us must be <= 1000000")
        return v

    @validator("laser_exp_us")
    def valid_laser_exp_us(cls, v):
        if v < 500:
            raise ValueError("laser_exp_us must be >= 500")
        elif v > 1000000:
            raise ValueError("laser_exp_us must be <= 1000000")
        return v

    @validator("laser_gain_percentage")
    def valid_laser_gain_percentage(cls, v):
        if v < 0:
            raise ValueError("laser_gain_percentage must be >= 0")
        elif v > 100:
            raise ValueError("laser_gain_percentage must be <= 100")
        return v

    @validator("led_panel_intensity_percentage")
    def valid_led_panel_intensity_percentage(cls, v):
        if v < 0:
            raise ValueError("led_panel_intensity_percentage must be >= 0")
        elif v > 100:
            raise ValueError("led_panel_intensity_percentage must be <= 100")
        return v

    @validator("laser_freq_hz")
    def valid_laser_freq_hz(cls, v):
        if v < 0:
            raise ValueError("laser_freq_hz must be >= 0")
        elif v > 100:
            raise ValueError("laser_freq_hz must be <= 100")
        return v

    @validator("stills_freq_hz")
    def valid_still_freq_hz(cls, v):
        if v < 0:
            raise ValueError("still_freq_hz must be >= 0")
        elif v > 5:
            raise ValueError("still_freq_hz must be <= 5")
        return v

    @validator("laser_min_range_cm")
    def valid_laser_min_range_cm(cls, v):
        if v < 0:
            raise ValueError("laser_min_range_cm must be >= 50")
        elif v > 2500:
            raise ValueError("laser_min_range_cm must be <= 1000")
        return v

    @validator("laser_max_range_cm")
    def valid_laser_max_range_cm(cls, v):
        if v < 0:
            raise ValueError("laser_max_range_cm must be >= 1000")
        elif v > 2500:
            raise ValueError("laser_max_range_cm must be <= 5000")
        return v

    @validator("index_of_refraction")
    def valid_index_of_refraction(cls, v):
        if v < 1.0:
            raise ValueError("index_of_refraction must be >= 1.0")
        elif v > 1.8:
            raise ValueError("index_of_refraction must be <= 1.8")
        return v

    @validator("stills_image_level")
    def valid_stills_image_level(cls, v):
        if v < 0:
            raise ValueError("stills_image_level must be >= 0")
        elif v > 2:
            raise ValueError("stills_image_level must be <= 2")
        return v

    @validator("stills_advanced_brightness")
    def valid_stills_advanced_brightness(cls, v):
        if v < 0:
            raise ValueError("stills_advanced_brightness must be >= 0")
        elif v > 1:
            raise ValueError("stills_advanced_brightness must be <= 1")
        return v

    @validator("stills_advanced_contrast")
    def valid_stills_advanced_contrast(cls, v):
        if v < 0:
            raise ValueError("stills_advanced_contrast must be >= 0")
        elif v > 1:
            raise ValueError("stills_advanced_contrast must be <= 1")
        return v

    def __str__(self):
        msg = ""
        msg += "\n    stills_exp_us: " + str(self.stills_exp_us)
        msg += "\n    laser_exp_us: " + str(self.laser_exp_us)
        msg += "\n    laser_freq_hz: " + str(self.laser_freq_hz)
        msg += "\n    stills_freq_hz: " + str(self.stills_freq_hz)
        msg += "\n    save_laser_images: " + str(self.save_laser_images)
        msg += "\n    laser_min_range_cm: " + str(self.laser_min_range_cm)
        msg += "\n    laser_max_range_cm: " + str(self.laser_max_range_cm)
        msg += "\n    index_of_refraction: " + str(self.index_of_refraction)
        msg += "\n    led_panel_intensity_percentage: " + str(
            self.led_panel_intensity_percentage
        )
        msg += "\n    laser_gain_percentage: " + str(self.laser_gain_percentage)
        msg += "\n    stills_image_level: " + str(self.stills_image_level)
        msg += "\n    stills_advanced_colour_mode: " + str(
            self.stills_advanced_colour_mode
        )
        msg += "\n    stills_advanced_colour_enhancement_lvl: " + str(
            self.stills_advanced_colour_enhancement_lvl
        )
        msg += "\n    stills_advanced_contrast_mode: " + str(
            self.stills_advanced_contrast_mode
        )
        msg += "\n    stills_advanced_contrast_lvl: " + str(
            self.stills_advanced_contrast_lvl
        )
        msg += "\n    stills_advanced_brightness: " + str(
            self.stills_advanced_brightness
        )
        msg += "\n    stills_advanced_contrast: " + str(self.stills_advanced_contrast)
        msg += "\n    stills_advanced_white_balance: " + str(
            self.stills_advanced_white_balance
        )
        msg += "\n    stills_advanced_adaptive_lighting: " + str(
            self.stills_advanced_adaptive_lighting
        )
        msg += "\n    stills_undistort: " + str(self.stills_undistort)
        msg += "\n    stills_save_original: " + str(self.stills_save_original)
        msg += "\n    stills_processed_image_format: " + str(
            self.stills_processed_image_format
        )
        msg += "\n    laser_disable_range_gating: " + str(
            self.laser_disable_range_gating
        )
        return msg


class EndpointIdConfig(BaseModel):
    base_path: str = "/data/data"
    mission_postfix: str = "default"
    log: str = "log/"
    stream: str = "stream/"
    xyz_laser: str = "laser/xyz/"
    sensor_laser: str = "laser/raw/"
    sensor_stills_raw: str = "stills/raw/"
    sensor_stills_processed: str = "stills/processed/"

    def __str__(self):
        msg = "\n    base_path: " + self.base_path
        msg += "\n    mission_postfix: " + self.mission_postfix
        msg += "\n    log: " + self.log
        msg += "\n    stream: " + self.stream
        msg += "\n    xyz_laser: " + self.xyz_laser
        msg += "\n    sensor_laser: " + self.sensor_laser
        msg += "\n    sensor_stills_raw: " + self.sensor_stills_raw
        msg += "\n    sensor_stills_processed: " + self.sensor_stills_processed
        return msg


class NetworkInput(BaseModel):
    ip_address: str = ""
    mode: str = ""
    driver: Optional[str] = None

    @validator("mode")
    def mode_is_valid(cls, v):
        if v.lower() not in ["tcp_client", "tcp_server", "udp", "com", "multicast"]:
            raise ValueError(
                "Mode needs to be TCP_CLIENT, TCP_SERVER, UDP, MULTICAST or COM in",
                "upper or lowercase characters.",
            )
        return v

    def __str__(self):
        msg = "\n    ip_address: " + self.ip_address
        msg += "\n    mode: " + self.mode
        if self.driver is not None:
            msg += "\n    driver: " + self.driver
        return msg


class Configuration(BaseModel):
    parameters: ScannerParamConfig = ScannerParamConfig()
    endpoint_id: EndpointIdConfig = EndpointIdConfig()
    pps_input: NetworkInput = NetworkInput()
    navigation_input: NetworkInput = NetworkInput()
    range_input: NetworkInput = NetworkInput()
    ip_address: str = "localhost"
    port: int = 4875
    log_path: str = "logs"

    def __init__(self, configuration_file: str = None):
        if configuration_file is None:
            super().__init__()
            return
        # check for correct_config yaml path
        configuration_file = Path(configuration_file)
        if not configuration_file.exists():
            raise FileNotFoundError(
                "Configuration file not found at {}".format(configuration_file)
            )
        stream = configuration_file.open("r")
        data = yaml.safe_load(stream)
        super().__init__(**data)

    def __str__(self):
        msg = "Configuration: " + self.ip_address
        msg += "\n  ip_address: " + self.ip_address
        msg += "\n  port: " + str(self.port)
        msg += "\n  navigation_input:" + str(self.navigation_input)
        msg += "\n  pps_input:" + str(self.pps_input)
        msg += "\n  log_path: " + self.log_path
        msg += "\n  parameters: " + str(self.parameters)
        msg += "\n  endpoint_id: " + str(self.endpoint_id)
        return msg
