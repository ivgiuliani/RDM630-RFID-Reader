#!/usr/bin/env python
"""
A Python module for reading rfid tags from a RDM630 125Khz receiver.
It supports both single reads from the receiver and continuous polling,
giving results back through callbacks. It also support autodiscovery
of the reader (assuming there's only one plugged in).
"""

import os
import sys
import serial

RFID_STRING_LENGTH = 14
USB_CONVERTER_PRODUCT_CODE = "403/6001/600"


def autodiscover():
    """Search the device through udev entries for a rdm630 and
    return the serial device string if we can find one or None
    otherwise"""
    from pyudev import Context

    context = Context()
    path = None

    for device in context.list_devices(subsystem="usb-serial"):
        # this check is not really reliable when multiple
        # usb-to-serial converters are attached (for example
        # when there's an arduino board plugged in too).
        if device.driver == "ftdi_sio":
            if device.parent["PRODUCT"] == USB_CONVERTER_PRODUCT_CODE:
                path = device["DEVPATH"].rsplit("/", 1)[1]
                break

    if not path:
        return None
    return os.path.join(context.device_path, path)


class RFIDObject(object):
    """A single rfid read from the serial device"""

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
        if self.start != self.START_BYTE or self != self.STOP_BYTE:
            return False

        checksum = self.calc_checksum()
        data_checksum = int(self.rawbytes[11] + self.rawbytes[12], 16)
        return checksum == data_checksum

    def get_tag(self):
        """Returns the current tag"""
        return "".join(self.tag)

    def calc_checksum(self):
        """Calculate string checksum"""
        tag = self.get_tag()
        pairs = [tag[i] + tag[i + 1] for i in range(0, len(tag), 2)]
        return reduce(lambda x, y: x ^ y, (int(x, 16) for x in pairs))


class RFIDReader(object):
    """Read tags coming from the serial device"""

    def __init__(self, port="/dev/ttyUSB0", baudrate=9600):
        self.port = port
        self.dev = None
        self.baudrate = baudrate

    def open(self):
        """Open the reader's serial port"""
        self.dev = serial.Serial(self.port,
                                 self.baudrate,
                                 bytesize=8,
                                 parity='N',
                                 stopbits=1)

    def close(self):
        """Close the reader's serial port"""
        if self.dev:
            self.dev.close()

    def poll(self, callback, timeout=0):
        """Constantly query the device and call `callback`
        when there's some data available or the timeout expires.
        The data passed to `callback` is already converted to
        an RFIDObject or is None if the timeout has expired
        """
        while True:
            callback(self.__query_device(timeout=timeout))

    def single_read(self, timeout=0):
        """Blocks until a single item is read from the device.
        A timeout value of 0 will make the read wait indefinitely
        until it read something, if `timeout` is greater than 0
        then it will wait at most `timeout` seconds. If timeout
        expires (i.e.: no value has been read) then it will
        return None.
        """
        return self.__query_device(timeout=timeout)

    def __query_device(self, timeout=0):
        """Awaits for data from the reader. Blocks until some
        data is received if `timeout` = 0, or wait at most `timeout`
        seconds if a timeout is specified. In case of timeout
        expiration returns None
        """
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
    """A small example callback"""
    if not rfid:
        print "timeout!"
    else:
        print "received tag: %s (checksum: %s)" % (
            rfid,
            hex(rfid.calc_checksum())
        )


def main(args):
    """Run a sample reader program"""
    if len(args) > 2:
        print "Usage: %s [<serialdevice>]" % args[0]
        return True

    try:
        port = args[1]
    except IndexError:
        port = autodiscover()

    if not port:
        sys.stderr.write("Couldn't autodiscover serial device\n")
        return True

    reader = RFIDReader(port)
    reader.open()
    try:
        reader.poll(sample_callback, 20)
    except KeyboardInterrupt:
        reader.close()

    return False


def test():
    """Some tests"""
    tag_orig_string = "62E3086CED"
    data = [
        '\x02',                                            # start byte
        '6', '2', 'E', '3', '0', '8', '6', 'C', 'E', 'D',  # tag
        '0', '8',                                          # checksum
        '\x03'                                             # stop byte
    ]
    checksum = 0x08

    rfid = RFIDObject(data)

    assert(rfid.is_valid() is True)
    assert(str(rfid) == tag_orig_string)
    assert(rfid.calc_checksum() == checksum)

if __name__ == "__main__":
    test()
    sys.exit(main(sys.argv))
