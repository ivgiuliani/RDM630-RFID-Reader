#!/usr/bin/env python
"""
A PAM module for user authentication (requires libpam-python to
work). It reads allowed rfid tags from ~/.rfidtags

In order to use it you need to have the rfidreader module in your
global python path and copy this module to /lib/security (and add
your tags in ~/.rfidtags, one per line).

Then you should configure PAM. If you want to authenticate *only*
with rfid then add the following lines before anything else in
/etc/pam.d/common-auth (on ubuntu systems):

  auth sufficient pam_python.so pam_rfidauth.py
  auth required pam_deny.so

If you want to fallback on password authentication on rfid failure
then just remove the second line.
"""

import os
import sys
import rfidreader

TIMEOUT_SECONDS = 5

def authenticate(username, rfid_tag):
    """Return true if the user has the given rfid tag stored
    in ~/.rfidtags"""
    tagfile = os.path.join(
        os.path.expanduser("~" + username),
        ".rfidtags"
    )
    tags = [tag.strip() for tag in file(tagfile).readlines()]
    return rfid_tag in tags

def read_tag(port=None, timeout=TIMEOUT_SECONDS):
    "Read a rfid tag from the rfid reader"
    port = port or rfidreader.autodiscover()

    reader = rfidreader.RFIDReader(port)
    reader.open()
    rfid = reader.single_read(timeout=timeout)
    reader.close()

    if not rfid:
        return None
    return rfid.get_tag()

def pam_sm_authenticate(pamh, flags, argv):
    try:
        user = pamh.get_user(None)
    except pamh.exception, e:
        return e.pam_result

    if not user:
        return pamh.PAM_USER_UNKNOWN

    try:
        port = argv[1]
    except IndexError:
        port = None

    rfid = read_tag(port=port)
    if not rfid:
        return pamh.PAM_AUTH_ERR

    if authenticate(user, rfid):
        return pamh.PAM_SUCCESS
    else:
        return pamh.PAM_AUTH_ERR

def pam_sm_setcred(pamh, flags, argv):
    return pamh.PAM_SUCCESS

if __name__ == "__main__":
    rfid = read_tag()
    if not rfid:
        print "can't read rfid"
        sys.exit(1)
    import pwd
    user = pwd.getpwuid(os.getuid())[0]
    auth_ok = authenticate(user, rfid)
    if not auth_ok:
        print "authentication failure"
    else:
        print "authentication ok"

