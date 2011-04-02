#!/usr/bin/env python
"""
Read a single value from the rfid device awaiting at
most TIMEOUT_SECONDS
"""

import sys
from rfidreader import RFIDReader

TIMEOUT_SECONDS = 5

def main(args):
    try:
        port = args[1]
    except IndexError:
        print "Usage: %s <port>" % args[0]
        return True

    reader = RFIDReader(port)
    reader.open()
    rfid = reader.single_read(timeout=TIMEOUT_SECONDS)
    if not rfid:
        print "Timeout expired!"
    else:
        print "Received rfid tag %s" % rfid
    reader.close()

    return False

if __name__ == "__main__":
    sys.exit(main(sys.argv))
