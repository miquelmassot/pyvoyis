# PyVoyis
Python library for controlling the Voyis Recon LS camera, strobes and laser system.

## Installation
Use pip to install the library:

```bash
pip install pyvoyis
```

## Usage
The library can be used as standalone or as a module. The following examples show how to use it as a module.

```python
from pyvoyis import VoyisAPI
api = VoyisAPI(args.ip, args.port)

# If you want the acquision to start straight away, you can request it
api.request_acquisition()

api.run()  # This will block until the acquisition is finished and the API disconnected

# From a different thread, you can request a stop
api.request_stop()
```

or you can call the API from the command line:

```bash
pyvoyis --ip 192.168.1.10 --port 4875
```

and it will start the acquisition and block until it's stopped with Ctrl+C.


## Known issues

### Time source does not work
I've set up a ZDA broadcast on port 4010. The scanner is connected to the same network and can ping the computer (192.168.1.71). The scanner is set to use the ZDA broadcast as its time source.

Message sent:

```json
{
    "message": "SetTimeTagSourceCmd",
    "payload": {
        "network": 2,
        "connection": "192.168.1.71:4010"
    }
}
```

Received:

```json
{
    "message": "AckRsp",
    "payload": {
        "accepted": false,
        "command_id": 263,
        "nack_error_code": 3,
        "nack_error_string": "Bad Parameter.",
        "api_version": "6.0.5.96dec0cc"
    }
}
```


### Nav source does not work

We've set up a PSONNAV broadcast on port 4003. The scanner is connected to the same network and can ping the computer (192.168.179.10). The scanner is set to use the PSONNAV broadcast as its nav source.

Message sent:

```json
{
    "message": "SetNavDataSourceCmd",
    "payload": {
        "network": 3,
        "protocol": 1,
        "connection": "192.168.179.10:4003"
    }
}
```

The scanner does not accept the nav source. The following error is returned:

```json
{
    "message": "AckRsp",
    "payload": {
        "accepted": false,
        "command_id": 35,
        "nack_error_code": 3,
        "nack_error_string": "Bad Parameter.",
        "api_version": "6.0.5.96dec0cc"
    }
}
```

Also tried with port only, and with either TCP_CLIENT or TCP_SERVER. Same result.

### Can the laser be disabled via software?
Answer unkown.

### What is the difference between local_value and remote_value in scanner_parameters?
Answer unkown.

### Temperature and humidity sensors reliable?
Only SCANNER_STATUS_INTERNAL_TEMP_CH works. Other report either 0 or 255.

### What are the max frequencies for cameras?
If the raw laser images are saved to disk, its frequency is currently limited to 1 Hz.

Can the frequency of laser images be larger than 1hz if there's enough time for stills? 
Can the laser images be saved as JPEG to save time?

### Laser calibration
Can we take images of the laser with both cameras? (e.g. leave the laser ON continuously and disable the strobes?)

## Laser in sunlight
Can we expect the laser to work in shoreline deployments? Should we default to collect raw laser images at 1 Hz?
