# Cooldown Scripts
This directory contains the files needed for a full system cooldown using the CS2 API

## Usage
The cooldown will be run through `cooldown.py`, which calls the other scripts

The user must choose the phases they want to use, by calling them in the main function in the order they want. Any pauses will also have to be added here. 

When using external API for DR system control, set the internal automation to Manual operation from the Control Software Gen. 2 Dashboard.

## Setup

`configuration.py` is needed for configuration:
- CS2 API address. If Python scripts are run on the same PC as the Control Software Gen2 core application, the default is 'https://localhost/api/v1'.
- Use of authentication, related variables
- SSL certificate path, if the certificate is not available through the system trust store
- Define whether the service booster pump B2 (HIPace80) is in use or not.

## Cooldown Scripts
All cooldown scripts are simply called by their name. Currently, the following phases have been written:
- Pump VC — `pump_vc_full.py`
- PT Cooling — `pt_cooling.py`
- PPC — `ppc_full.py`
- Condensing — `condensing.py`
- System Warmup — `warm_system.py`


## Scripts
In addition to the cooldown scripts, the following files add functionality to the cooldown:

- `cooldown.py` — Runner script for the cooldown/warmup.
- `functions.py` — Contains functions used to communicate with the CS2 API. 

## Notes on control system

- Cooldown script assumes that the Gas-Handling System is an Industrial version (the most full-featured product version)
- Liquid nitrogen trap between valves V401 and V402 is assumed to be in use
- Scripts will work on other systems as well, but some device calls will report an exception if a featured device is missing,
for example V300 series valves. These exceptions won't interfere with script execution and can be ignored.

