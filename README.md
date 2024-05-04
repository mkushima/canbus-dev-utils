# canbus-dev-utils

This Python project aims to provide developer tools for working with the SocketCAN interface. 

## Features
- UDS Server: "Mocked" UDS Server
- UDS Client: Utility for sending UDS requests
- SocketCAN Interface Management: Script to manage SocketCAN interfaces, including setting up, tearing down, and configuring.

## Requirement

- Python 3.10
- For kernel version prior to 5.10.0, this [out-of-tree loadable kernel module](https://github.com/hartkopp/can-isotp) can be compiled and loaded in the Linux kernel, enabling ISO-TP sockets

## Instalation
- Clone this repository and create a virtual env
- Install the package in editable mode: `python -m pip install -e .`

## Usage
- Start UDS Server
```
uds_server -i vcan0 --rx_id 18DAEE4A --tx_id 18DA4AEE
```

- Run UDS Client
```
uds_client
```
