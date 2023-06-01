"""
Copyright (c) 2023, Miquel Massot
All rights reserved.
Licensed under the GPLv3 License.
See LICENSE.md file in the project root for full license information.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, validator


class ApiParamStillsConfig(BaseModel):
    undistort: bool = False
    save_original: bool = False
    processed_image_format: str = "jpg"

    @validator("processed_image_format")
    def valid_processed_image_format(cls, v):
        if v not in ["jpg", "tiff"]:
            raise ValueError('processed_image_format must be "jpg" or "tiff"')
        return v


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
    laser_disable_range_gating: bool = False

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


class EndpointIdConfig(BaseModel):
    log: str = "/data/data/default/log/"
    stream: str = "/data/data/default/stream/"
    xyz_laser: str = "/data/data/default/laser/xyz/"
    sensor_laser: str = "/data/data/default/laser/raw/"
    sensor_stills_raw: str = "/data/data/default/stills/raw/"
    sensor_stills_processed: str = "/data/data/default/stills/processed/"


class Configuration(BaseModel):
    api_param_stills: ApiParamStillsConfig = ApiParamStillsConfig()
    scanner_param: ScannerParamConfig = ScannerParamConfig()
    endpoint_id: EndpointIdConfig = EndpointIdConfig()
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
