#!/usr/bin/env python

import sys
import serial
import time

RFID_BYTES = 14
START_BYTE = 0x02
STOP_BYTE = 0x03

class RFIDReader(object):
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600):
        self.dev = serial.Serial(port, 9600, bytesize=8, parity='N', stopbits=1)

    def run(self):
        try:
            while True:
                self.query_device()
                time.sleep(1)
        except KeyboardInterrupt:
            self.dev.close()

    def query_device(self):
        raw = self.dev.read(RFID_BYTES)
        if len(raw) == RFID_BYTES:
            rfid = [ord(x) for x in raw]

            start, stop = rfid[0], rfid[-1]
            if start == START_BYTE and stop == STOP_BYTE:
                tag = get_rfid_tag(rfid[1:11])
                checksum = calc_checksum(tag)

                print "TAG: %s CALCULATED CHECKSUM: %s (data checksum: 0x%s)" % (
                    readable_tag(tag),
                    hex(checksum),
                    raw[11] + raw[12],
                )
            else:
                print "INVALID"

def readable_tag(tag):
    string = []
    for x in tag:
        if x < 10:
            string.append(chr(ord('0') + x))
        else:
            string.append(chr(ord('A') + x - 10))
    return "".join(string)

def calc_checksum(rfid_tag):
    pairs = []
    for i in range(0, 10, 2):
        pairs.append(rfid_tag[i] * 16 + rfid_tag[i + 1])
    return pairs[0] ^ pairs[1] ^ pairs[2] ^ pairs[3] ^ pairs[4]

def get_rfid_tag(rawbytes):
    DEC_LETTER_BASE = 0x30
    HEX_LETTER_BASE = 0x37

    rfid_tag = []
    for byte in rawbytes:
        if byte >= (HEX_LETTER_BASE + 0x0A):
            rfid_tag.append(byte - HEX_LETTER_BASE)
        else:
            rfid_tag.append(byte - DEC_LETTER_BASE)

    return rfid_tag

def main(args):
    if len(args) != 2:
        print "Usage: %s <serialdevice>" % args[0]
        return True

    port = args[1]
    reader = RFIDReader(port)
    reader.run()

    return False

def test():
    orig = [0x6, 0x2, 0xe, 0x3, 0x0, 0x8, 0x6, 0xC, 0xE, 0xD]
    orig_string = "62E3086CED"
    data = [0x36, 0x32, 0x45, 0x33, 0x30, 0x38, 0x36, 0x43, 0x45, 0x44]
    checksum = 0x08

    rfid = get_rfid_tag(data)

    assert(rfid == orig)
    assert(readable_tag(rfid) == orig_string)
    assert(calc_checksum(rfid) == checksum)

if __name__ == "__main__":
    test()
    sys.exit(main(sys.argv))
