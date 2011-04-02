#!/usr/bin/env python
"""
A simple notifier that shows a bubble notify when a rfid
tag is received
"""

import sys
import pynotify
from rfidreader import RFIDReader

capabilities = {'actions':             False,
                'body':                False,
                'body-hyperlinks':     False,
                'body-images':         False,
                'body-markup':         False,
                'icon-multi':          False,
                'icon-static':         False,
                'sound':               False,
                'image/svg+xml':       False,
                'private-synchronous': False,
                'append':              False,
                'private-icon-only':   False}

def init_pynotify():
    caps = pynotify.get_server_caps()
    if not caps:
        print "Failed to receive server caps."
        sys.exit(True)

    for cap in caps:
        capabilities[cap] = True


def callback(rfid):
    notify = pynotify.Notification(
        "RFID tag received",
        rfid.get_tag()
    )
    notify.show()

def main(args):
    try:
        port = args[1]
    except IndexError:
        print "Usage: %s <port>" % args[0]
        return True

    init_pynotify()
    reader = RFIDReader(port)
    reader.open()
    try:
        reader.poll(callback)
    except KeyboardInterrupt:
        reader.close()

    return False

if __name__ == "__main__":
    sys.exit(main(sys.argv))
