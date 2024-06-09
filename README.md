# canbus-dev-utils

This Python project aims to provide developer tools for working with the SocketCAN interface. 

## Features
- UDS Server: "Mocked" UDS Server
- UDS Client: Utility for sending UDS requests
- SocketCAN Interface Management: Script to manage SocketCAN interfaces, including setting up, tearing down, and configuring.
- Send CAN messages: Utility for sending CAN messages with specified PGNs and SPNs using the provided DBC file.

## Requirement

- Python 3.10
- For kernel version prior to 5.10.0, this [out-of-tree loadable kernel module](https://github.com/hartkopp/can-isotp) can be compiled and loaded in the Linux kernel, enabling ISO-TP sockets

## Instalation
- Clone this repository and create a virtual env
- Install the package in editable mode: `python -m pip install -e .`

## Usage
- Configure the SocketCAN
```
scripts/config-socketcan.sh --up -i 0 --virtual
```

- Start UDS Server
```
uds_server -ch vcan0 --rx_id 18DAEE4A --tx_id 18DA4AEE
```

- Run UDS Client
```
uds_client -ch vcan0 --rx_id 18DA4AEE --tx_id 18DAEE4A
```

- Send CAN messages once
```
send_can_msg -ch vcan0 --dbc path/to/sample_j1939.dbc "{ 'EEC1' : { 'EngSpeed': 1610.87, }, 'CCVS' : { 'WheelBasedVehicleSpeed' : 54.7, 'CruiseCtrlSetSpeed': 55, } }"
```

- Send CAN messages periodically
```
send_can_msg -ch vcan0 --dbc path/to/sample_j1939.dbc -t 10 "{ 'EEC1' : { 'EngSpeed': 1610.87, }, 'CCVS' : { 'WheelBasedVehicleSpeed' : 54.7, 'CruiseCtrlSetSpeed': 55, } }"
```
