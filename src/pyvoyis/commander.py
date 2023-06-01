"""
Copyright (c) 2023, Miquel Massot
All rights reserved.
Licensed under the GPLv3 License.
See LICENSE.md file in the project root for full license information.
"""

from pyvoyis.api500 import API500Command


class VoyisCommander:
    ping_api = API500Command("PingApiCmd")
    query_api_version = API500Command(
        "QueryAPIVersionCmd", expected_response=["APIVersionNot"]
    )
    list_scanners = API500Command(
        "ListScannersCmd", expected_response=["ScannerListNot"]
    )
    check_for_scanner = API500Command(
        "CheckForScannerCmd", needs_payload=True, expected_response=["ScannerListNot"]
    )
    connect_scanner = API500Command(
        "ConnectScannerCmd",
        needs_payload=True,
        timeout_s=30,
        expected_response=["ScannerListNot, PendingCmdStatusNot"],
    )
    disconnect = API500Command("DisconnectCmd", expected_response=["ScannerListNot"])
    shutdown = API500Command("ShutdownCmd", timeout_s=30)
    query_scanner_status = API500Command(
        "QueryScannerStatusCmd",
        expected_response=["ScannerStatusNot", "LeakDetectionNot"],
    )
    query_scanner_parameters = API500Command(
        "QueryScannerParametersCmd", expected_response=["ScannerParametersNot"]
    )
    apply_local_scanner_parameters = API500Command(
        "ApplyLocalScannerParametersCmd",
        expected_response=["ScannerStatusNot", "ScannerParametersNot"],
    )
    set_local_scanner_parameters = API500Command(
        "SetLocalScannerParametersCmd",
        needs_payload=True,
        expected_response=["ScannerParametersNot"],
    )
    calculate_and_set_ior = API500Command("CalculateAndSetIORCmd", needs_payload=True)
    start_scanner = API500Command(
        "StartScannerCmd", needs_payload=True, expected_response=["ScannerStatusNot"]
    )
    stop_scanner = API500Command(
        "StopScannerCmd", expected_response=["ScannerStatusNot"]
    )
    enable_nas = API500Command("EnableNASCmd")
    disable_nas = API500Command("DisableNASCmd")
    enable_local_storage = API500Command("EnableLocalStorageCmd")
    disable_local_storage = API500Command("DisableLocalStorageCmd")
    set_remote_endpoints = API500Command("SetRemoteEndpointsCmd", needs_payload=True)
    query_api_configuration = API500Command(
        "QueryAPIConfigurationCmd", expected_response=["APIConfigurationNot"]
    )
    set_api_configuration = API500Command(
        "SetAPIConfigurationCmd",
        needs_payload=True,
        expected_response=["APIConfigurationNot"],
    )
    set_time_tag_source = API500Command(
        "SetTimeTagSourceCmd",
        needs_payload=True,
        expected_response=["ScannerStatusNot"],
    )
    set_endpoints = API500Command(
        "SetEndpointsCmd",
        needs_payload=True,
        expected_response=["EndpointConfigurationNot"],
    )
    set_log_saving = API500Command("SetLogSavingCmd", needs_payload=True)
    network_time_sync = API500Command(
        "NetworkTimeSyncCmd", expected_response=["ScannerStatusNot"]
    )
    set_stills_metadata = API500Command("SetStillsMetadataCmd", needs_payload=True)
    set_nav_data_source = API500Command("SetNavDataSourceCmd", needs_payload=True)
    set_range_data_source = API500Command("SetRangeDataSourceCmd", needs_payload=True)
    load_correction_model = API500Command(
        "LoadCorrectionModelCmd",
        needs_payload=True,
        expected_response=["CorrectionModelLoadNot"],
    )
    query_correction_models = API500Command(
        "QueryCorrectionModelsCmd", expected_response=["CorrectionModelLoadNot"]
    )
