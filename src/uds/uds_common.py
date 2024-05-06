#!/usr/bin/env python3

from enum import Enum

class ServiceID(Enum):
    DIAGNOSTIC_SESSION_CONTROL = 0x10
    ECU_RESET = 0x11
    READ_DATA_BY_IDENTIFIER = 0x22
    READ_DATA_BY_PERIODIC_IDENTIFIER = 0x2A
    DYNAMICALLY_DEFINE_DATA_IDENTIFIER = 0x2C
    WRITE_DATA_BY_IDENTIFIER = 0x2E
    INPUT_OUTPUT_CONTROL_BY_IDENTIFIER = 0x2F
    ROUTINE_CONTROL = 0x31
    REQUEST_DOWNLOAD = 0x34
    TRANSFER_DATA = 0x36
    REQUEST_UPLOAD = 0x35
    REQUEST_TRANSFER_EXIT = 0x37
    SECURITY_ACCESS = 0x27
    COMMUNICATION_CONTROL = 0x28

    def __str__(self):
        return hex(self.value)
