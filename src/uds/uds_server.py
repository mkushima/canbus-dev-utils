"""
Module for managing Unified Diagnostic Services (UDS) requests.

Classes:
    UDSServer: Manages UDS requests over the CAN bus. Currently, it handles
    only Read Data By Identifier and Write Data By Identifier.

Usage:
    To use the UDSServer class, instantiate it with the required parameters such as
    the CAN channel (e.g.: vcan0), receive identifier (RX ID), and transmit identifier (TX ID).
    Optionally, provide UDS data to be served.
    Additional keyword arguments can be used to configure features like FD mode, padding,
    Flow Control (FC) STmin, and Block Size (BS).
    Once instantiated, call the 'run' method to start the main loop for processing UDS requests.

Example:
    # Import the UDSServer class from the module
    from your_module_name import UDSServer

    # Instantiate the UDSServer class with the required parameters
    uds_server = UDSServer(can_channel="can0", rx_id=18DAEE4A, tx_id=0x18DA4AEE)

    # Optionally, provide UDS data to be served
    uds_data = {
        0x1234: bytearray(b'\x01\x02\x03\x04'),
        0x5678: bytearray(b'\x05\x06\x07\x08'),
    }
    uds_server = UDSServer(can_channel="can0", rx_id=18DAEE4A, tx_id=0x18DA4AEE, uds_data=uds_data)

    # Additional keyword arguments can be used to configure additional features
    uds_server = UDSServer(
        can_channel="can0",
        rx_id=18DAEE4A,
        tx_id=0x18DA4AEE,
        uds_data=uds_data,
        is_fd=True,
        padding=0xAA,
        fc_stmin=10,
        fc_bs=5
    )

    # Start the main loop for processing UDS requests
    uds_server.run()
"""
import copy
import isotp

from logger import MyLogger
from uds.uds_common import ServiceID


# Logger setup
logger = MyLogger(__name__)


class UDSServer:
    """
    Class for managing Unified Diagnostic Services (UDS) requests.
    """
    DUMMY_DATA = {
        0x0001: bytearray(b'\x01'),
        0x0007: bytearray(b'\x07\x07\x07\x07\x07\x07\x07'),
        0x0030: 200 * bytearray(b'\x30'),
        0xF190: bytearray('5YJSA1DG9DFP14705', 'utf-8'), # VIN
    }

    DEFAULT_TXPAD = 0xAA
    DEFAULT_ST_MIN = 10 # ms
    DEFAULT_BS = 5

    def __init__(
            self, can_channel: str, rx_id: int, tx_id: int, uds_data: dict = None,
            **kwargs,
        ):
        """
        Initialize the UDSServer instance.

        Args:
            can_channel (str): The CAN channel to bind the server to.
            rx_id (int): The receive identifier (RX ID) for receiving ISO-TP frames.
            tx_id (int): The transmit identifier (TX ID) for transmitting ISO-TP frames.
            uds_data (dict, optional): Dict containing UDS data to be served. Defaults to None.
            **kwargs: Additional keyword arguments:
                is_fd (bool): Flag indicating whether FD mode is enabled. Defaults to False.
                padding (int): The transmit padding byte value. Defaults to UDSServer.DEFAULT_TXPAD.
                fc_stmin (int): The FC STmin value. Defaults to UDSServer.DEFAULT_ST_MIN.
                fc_bs (int): The FC - Block Size (BS) value. Defaults to UDSServer.DEFAULT_BS.
        """
        if uds_data is None:
            logger.warning("No 'UDS data' has been provided by user. Using dummy data!")
            self.data = copy.deepcopy(UDSServer.DUMMY_DATA)
        else:
            self.data = uds_data

        is_fd = kwargs.get('is_fd', False)
        padding = kwargs.get('padding', UDSServer.DEFAULT_TXPAD)
        fc_stmin = kwargs.get('fc_stmin', UDSServer.DEFAULT_ST_MIN)
        fc_bs = kwargs.get('fc_bs', UDSServer.DEFAULT_BS)

        logger.info(
            "UDS Server config:" +
            f"\n\tChannel = {can_channel}" +
            f"\n\tRx ID = 0x{rx_id:X}" +
            f"\n\tTx ID = 0x{tx_id:X}" +
            f"\n\tPadding = 0x{padding:X}" +
            f"\n\tFlow Control - STmin = {fc_stmin}" +
            f"\n\tFlow Control - Block size = {fc_bs}"
        )

        # Setting a timeout to avoid getting stuck forever, while waiting for a request.
        self.server = isotp.socket(timeout=1)

        # Configure the Tx padding
        self.server.set_opts(txpad=padding)

        # Flow Control options
        self.server.set_fc_opts(stmin=fc_stmin, bs=fc_bs)

        if is_fd:
            logger.info("FD mode is enabled")
            self.server.set_ll_opts(
                mtu=isotp.socket.LinkLayerProtocol.CAN_FD,
                tx_dl=64,
                tx_flags=0x01,
            )

        isotp_address = isotp.Address(
            addressing_mode=isotp.AddressingMode.Normal_29bits,
            rxid=rx_id,
            txid=tx_id,
        )

        self.server.bind(interface=can_channel, address=isotp_address)

        self.service_handlers = {
            ServiceID.READ_DATA_BY_IDENTIFIER: self._handle_read_data_by_id,
            ServiceID.WRITE_DATA_BY_IDENTIFIER: self._handle_write_data_by_id,
        }

    def run(self):
        """
        Main loop for running the UDSServer instance.
        """
        try:
            raw_request = self.server.recv()
        except TimeoutError:
            # Nothing has been received...
            return

        # TODO: Check the size first...
        try:
            sid = ServiceID(UDSServer.get_sid(raw_request))
        except ValueError:
            logger.error(
                f"Sending Negative Response - Unknown SID: {hex(UDSServer.get_sid(raw_request))}")
            self._send_negative_response(UDSServer.get_sid(raw_request))
            return

        if sid not in self.service_handlers:
            logger.error(f"Sending Negative Response - No handler found for SID: {hex(sid.value)}")
            self._send_negative_response(sid.value)
            return

        self.service_handlers[sid](raw_request)

    @staticmethod
    def get_sid(raw_request):
        """
        Get the Service Identifier (SID) from a raw request.

        Args:
            raw_request: The raw request data.

        Returns:
            int: The Service Identifier (SID) extracted from the raw request.
        """
        return raw_request[0]

    @staticmethod
    def get_did(raw_request):
        """
        Get the Data Identifier (DID) from a raw request.

        Args:
            raw_request: The raw request data.

        Returns:
            int: The Data Identifier (DID) extracted from the raw request.
        """
        return (raw_request[1] << 8) + raw_request[2]

    def _handle_read_data_by_id(self, raw_request):
        """
        Handle the Read Data By Identifier service.

        Args:
            raw_request: The raw request data.
        """
        did = UDSServer.get_did(raw_request)

        if did not in self.data:
            logger.error(f'Sending Negative Response - SID: 0x22 - DID {hex(did)} not found')
            # TODO: Sending the proper NRC
            self._send_negative_response(rej_sid=UDSServer.get_sid(raw_request))
            return

        logger.info(f'SID: 0x22 - Sending DID {hex(did)} content')
        self.server.send(
            b'\x62' +
            did.to_bytes(length=2, byteorder='big') +
            self.data[did]
        )

    def _handle_write_data_by_id(self, raw_request):
        """
        Handle the Write Data By Identifier service.

        Args:
            raw_request: The raw request data.
        """
        did = UDSServer.get_did(raw_request)

        if did not in self.data:
            logger.error(f'Sending Negative Response - SID: 0x2E - DID {hex(did)} not found')
            # TODO: Sending the proper NRC
            self._send_negative_response(rej_sid=UDSServer.get_sid(raw_request))
            return

        logger.info(f'SID: 0x2E - Updating DID {hex(did)}')
        self.data[did] = raw_request[3:]

        # TODO: Check if this is the correct payload format
        self.server.send(
            b'\x6E' +
            did.to_bytes(length=2, byteorder='big')
        )

    def _send_negative_response(self, rej_sid: int):
        """
        Sending a Negative Response with NRC as General Reject.

        Args:
            rej_sid (int): The Service Identifier (SID) for the negative response.
        """
        isinstance(rej_sid, int)

        self.server.send(b'\x7F' + rej_sid.to_bytes(length=1, byteorder='big') + b'\x10')
