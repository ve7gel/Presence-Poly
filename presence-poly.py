#!/usr/bin/env python3
import udi_interface
import sys
from nodes import presence_ctl

LOGGER = udi_interface.LOGGER
Custom = udi_interface.Custom


if __name__ == "__main__":
    try:
        polyglot = udi_interface.Interface([])
        polyglot.start()
        control = presence_ctl.Controller(polyglot, 'controller', 'controller', 'presence')
        polyglot.runForever()

    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)
