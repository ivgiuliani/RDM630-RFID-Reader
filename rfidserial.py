#!/usr/bin/env python

import sys
import serial
import time

RFID_BYTES = 14
START_BYTE = 0x02
STOP_BYTE = 0x03

def to_rawbytes(serial_string):
    return [ord(x) for x in serial_string]

class RFIDObject(object):
    def __init__(self, rawbytes):
        self.rawbytes = rawbytes

    def is_valid(self):
        # TODO: checksum
        return self.rawbytes[0] == START_BYTE and \
               self.rawbytes[-1] == STOP_BYTE

    def readable_tag(self):
        string = []
        for x in self.get_rfid_tag():
            if x < 10:
                string.append(chr(ord('0') + x))
            else:
                string.append(chr(ord('A') + x - 10))
        return "".join(string)
    
    def calc_checksum(self):
        TAG_LENGTH = 10
        pairs = []
        tag = self.get_rfid_tag()
        for i in range(0, TAG_LENGTH, 2):
            pairs.append(tag[i] * 16 + tag[i + 1])
        return reduce(lambda x, y: x ^ y, pairs)
    
    def get_rfid_tag(self):
        DEC_LETTER_BASE = 0x30
        HEX_LETTER_BASE = 0x37

        rfid_tag = []
        for byte in self.rawbytes[1:11]:
            if byte >= (HEX_LETTER_BASE + 0x0A):
                rfid_tag.append(byte - HEX_LETTER_BASE)
            else:
                rfid_tag.append(byte - DEC_LETTER_BASE)

        return rfid_tag


class RFIDReader(object):
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600):
        self.port = port
        self.baudrate = baudrate

    def open(self):
        self.dev = serial.Serial(self.port,
                                 self.baudrate,
                                 bytesize=8,
                                 parity='N',
                                 stopbits=1)

    def close(self):
        self.dev.close()

    def run(self):
        try:
            while True:
                self.query_device()
                time.sleep(1)
        except KeyboardInterrupt:
            self.close()

    def query_device(self):
        raw = self.dev.read(RFID_BYTES)
        if len(raw) != RFID_BYTES:
            return

        rfid = RFIDObject(to_rawbytes(raw))
        if not rfid.is_valid():
            print "INVALID"
            return

        tag = rfid.get_rfid_tag()
        checksum = rfid.calc_checksum()

        print "TAG: %s CALCULATED CHECKSUM: %s (data checksum: 0x%s)" % (
            rfid.readable_tag(),
            hex(checksum),
            (raw[11],raw[12]),
        )


def main(args):
    if len(args) != 2:
        print "Usage: %s <serialdevice>" % args[0]
        return True

    port = args[1]
    reader = RFIDReader(port)
    reader.open()
    reader.run()

    return False

def test():
    tag_orig = [0x6, 0x2, 0xe, 0x3, 0x0, 0x8, 0x6, 0xC, 0xE, 0xD]
    tag_orig_string = "62E3086CED"
    data = [0x02, 0x36, 0x32, 0x45, 0x33, 0x30, 0x38, 0x36, 0x43, 0x45, 0x44, 0x04, 0x0A, 0x03]
    checksum = 0x08

    rfid = RFIDObject(data)

    assert(rfid.is_valid() == True)
    assert(rfid.get_rfid_tag() == tag_orig)
    assert(rfid.readable_tag() == tag_orig_string)
    assert(rfid.calc_checksum() == checksum)

if __name__ == "__main__":
    test()
    sys.exit(main(sys.argv))
