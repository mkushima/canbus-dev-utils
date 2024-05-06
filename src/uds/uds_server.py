#!/usr/bin/env python3

import isotp

from uds.uds_common import ServiceID

class UDSServer:
    dummy_data = {
        0x2001: bytearray(b'\x01\x02\x03\x04\x05\x06\x07\x08'),
        0x2002: bytearray(b'\x02\x02\x02'),
        0x2003: 40 * bytearray(b'\x03'),
        0x2004: 50 * bytearray(b'\x04'),
        0x2005: 200 * bytearray(b'\x05'),
        0xF190: bytearray('5YJSA1DG9DFP14705', 'utf-8'), # VIN
    }

    def __init__(self, can_channel: str, rx_id: int, tx_id: int, is_fd: bool = False):
        # Reference: https://readthedocs.org/projects/can-isotp/downloads/pdf/stable/
        self.server = isotp.socket(timeout=1)

        # Configure the Tx padding
        self.server.set_opts(txpad=0xAA)

        # Flow Control options
        self.server.set_fc_opts(stmin=5, bs=10)

        if is_fd:
            # Link Layer options
            # TODO: Check if `tx_flags=0x01` really enables the BRS
            # Reference: https://elixir.bootlin.com/linux/latest/source/include/uapi/linux/can.h#L160
            # https://stackoverflow.com/questions/44851066/what-is-the-flags-field-for-in-canfd-frame-in-socketcan
            self.server.set_ll_opts(mtu=isotp.socket.LinkLayerProtocol.CAN_FD, tx_dl=64, tx_flags=0x01)

        isotp_address = isotp.Address(addressing_mode=isotp.AddressingMode.Normal_29bits, rxid=rx_id, txid=tx_id)
        self.server.bind(interface=can_channel, address=isotp_address)

        self.service_handlers = {
            ServiceID.READ_DATA_BY_IDENTIFIER: lambda req: self._handle_read_data_by_id(req),
            ServiceID.WRITE_DATA_BY_IDENTIFIER: lambda req: self._handle_write_data_by_id(req),
        }

    def send_negative_response(self, rej_sid: int):
        """
        Sending a Negative Response with NRC as General Reject
        """
        isinstance(rej_sid, int)

        self.server.send(b'\x7F' + rej_sid.to_bytes(length=1, byteorder='big') + b'\x10')

    @staticmethod
    def get_did(payload):
        return (payload[1] << 8) + payload[2]

    def _handle_read_data_by_id(self, req):
        did = UDSServer.get_did(req)

        if did not in self.dummy_data:
            print(f'[ERROR] Sending Negative Response - SID: 0x22 - DID {hex(did)} not found')
            # TODO: Sending the proper NRC
            self.send_negative_response(rej_sid=req[0])
            return

        print(f'SID: 0x22 - Sending DID {hex(did)} content')
        self.server.send(
            b'\x62' +
            did.to_bytes(length=2, byteorder='big') +
            self.dummy_data[did]
        )

    def _handle_write_data_by_id(self, req):
        did = UDSServer.get_did(req)

        if did not in self.dummy_data:
            print(f'[ERROR] Sending Negative Response - SID: 0x2E - DID {hex(did)} not found')
            # TODO: Sending the proper NRC
            self.send_negative_response(rej_sid=req[0])
            return

        print(f'SID: 0x2E - Updating DID {hex(did)}')
        self.dummy_data[did] = req[3:]

        # TODO: Check if this is the correct payload format
        self.server.send(
            b'\x6E' +
            did.to_bytes(length=2, byteorder='big')
        )

    def run(self):
        try:
            req = self.server.recv()
        except TimeoutError:
            # Nothing has been received...
            return

        # TODO: Check the size first...
        try:
            sid = ServiceID(req[0])
        except ValueError:
            print(f'[ERROR] Sending Negative Response - Unknown SID: {hex(req[0])}')
            self.send_negative_response(req[0])
            return

        if sid not in self.service_handlers:
            print(f'[ERROR] Sending Negative Response - No handler found for SID: {hex(sid.value)}')
            self.send_negative_response(sid.value)
            return

        self.service_handlers[sid](req)
