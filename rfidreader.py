#!/usr/bin/env python

import sys
import serial

RFID_STRING_LENGTH = 14

class RFIDObject(object):
    "A single rfid read from the serial device"

    START_BYTE = 0x02
    STOP_BYTE = 0x03

    def __init__(self, rawbytes):
        self.rawbytes = rawbytes
        self.start, self.stop = ord(rawbytes[0]), ord(rawbytes[-1])
        self.tag = rawbytes[1:11]
        self.checksum = rawbytes[11:13]

    def __str__(self):
        return self.get_tag()

    def is_valid(self):
        """Returns true if both the packet is valid (the start
        and stop bytes are correct) and the checksum matches
        """
        if self.start != RFIDObject.START_BYTE or \
           self.stop  != RFIDObject.STOP_BYTE:
            return False

        checksum = self.calc_checksum()
        data_checksum = int(self.rawbytes[11] + self.rawbytes[12], 16)
        return checksum == data_checksum

    def get_tag(self):
        "Returns the current tag"
        return "".join(self.tag)

    def calc_checksum(self):
        "Calculate string checksum"
        pairs = []
        tag = self.get_tag()
        for i in range(0, len(tag), 2):
            pairs.append(tag[i] + tag[i + 1])

        return int(pairs[0], 16) ^ \
               int(pairs[1], 16) ^ \
               int(pairs[2], 16) ^ \
               int(pairs[3], 16) ^ \
               int(pairs[4], 16)


class RFIDReader(object):
    "Read tags coming from the serial device"

    def __init__(self, port="/dev/ttyUSB0", baudrate=9600):
        self.port = port
        self.dev = None
        self.baudrate = baudrate

    def open(self):
        self.dev = serial.Serial(self.port,
                                 self.baudrate,
                                 bytesize=8,
                                 parity='N',
                                 stopbits=1)

    def close(self):
        if self.dev:
            self.dev.close()

    def poll(self, callback, timeout=None):
        """Constantly query the device and call `callback`
        when there's some data available. The data passed
        to `callback` is already converted to an RFIDObject
        """
        self.dev.timeout = timeout
        while True:
            callback(self.__query_device())

    def single_read(self, timeout=0):
        """Blocks until a single item is read from the device.
        If `timeout` is greater than 0 then it will wait at
        most `timeout` seconds. If timeout expires (i.e.: no
        value has been read) then it will return None.
        """
        return self.__query_device(timeout=timeout)

    def __query_device(self, timeout = 0):
        assert(timeout >= 0)
        if timeout == 0:
            self.dev.timeout = None
        else:
            self.dev.timeout = timeout

        raw = self.dev.read(RFID_STRING_LENGTH)
        if len(raw) != RFID_STRING_LENGTH:
            return

        rfid = RFIDObject(raw)
        if not rfid.is_valid():
            # invalid read, ignore
            return

        return rfid


def sample_callback(rfid):
    print "received tag: %s (checksum: %s)" % (
        rfid,
        hex(rfid.calc_checksum())
    )

def main(args):
    if len(args) != 2:
        print "Usage: %s <serialdevice>" % args[0]
        return True

    port = args[1]
    reader = RFIDReader(port)
    reader.open()
    try:
        reader.poll(sample_callback)
    except KeyboardInterrupt:
        reader.close()

    return False

def test():
    tag_orig = [0x6, 0x2, 0xe, 0x3, 0x0, 0x8, 0x6, 0xC, 0xE, 0xD]
    tag_orig_string = "62E3086CED"
    data = ['\x02', '6', '2', 'E', '3', '0', '8', '6', 'C', 'E', 'D', '0', '8', '\x03']
    checksum = 0x08

    rfid = RFIDObject(data)

    assert(rfid.is_valid() == True)
    assert(str(rfid) == tag_orig_string)
    assert(rfid.calc_checksum() == checksum)

if __name__ == "__main__":
    test()
    sys.exit(main(sys.argv))
