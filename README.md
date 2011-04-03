RDM630 RFID Reader
==================

This is a python module for reading values from a RDM630 rfid receiver.
It supports both a single read from the receiver and continuous polling
(giving results back through callbacks).
It also support autodiscovery of the reader (assuming there's only one
plugged in).

### Requirements:
* pyserial
* pyudev

### Examples
I included a small set of example modules in the `examples/` directory.

#### singleread.py
An example of doing a single read from the rfid reader.

#### gnome-notification.py
Shows a OSD notification whenever a tag is read by the receiver.
Requires pyinotify.

#### pam\_rfidauth.py
This is probably the most interesting application example. It is a complete
PAM authentication module for authentication through RFID tags.
Configuration instructions are inside the source file.
