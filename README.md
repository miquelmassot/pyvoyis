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


## Notes

If the IP address of the time source or nav source are not "pingable" the device does not report and AckRsp. Sometimes it might realise and return a "Bad parameter" error.

### Can the laser be disabled via software?
Set laser intensity to zero or laser camera frequency to 0 Hz.

### What is the difference between local_value and remote_value in scanner_parameters?
Answer unkown.

### What are the max frequencies for cameras?
If the raw laser images are saved to disk, its frequency is currently limited to 1 Hz.

Can the frequency of laser images be larger than 1hz if there's enough time for stills? 
Can the laser images be saved as JPEG to save time?

### Laser calibration
Can we take images of the laser with both cameras? (e.g. leave the laser ON continuously and disable the strobes?)

## Laser in sunlight
Can we expect the laser to work in shoreline deployments? Should we default to collect raw laser images at 1 Hz?
