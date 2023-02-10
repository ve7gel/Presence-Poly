#!/usr/bin/env python3
import udi_interface
import sys
from nodes import presence_ctl

LOGGER = udi_interface.LOGGER
Custom = udi_interface.Custom
Version = '3.0.0'

if __name__ == "__main__":
    try:
        polyglot = udi_interface.Interface([])
        polyglot.start()
        control = presence_ctl.Controller(polyglot, 'controller', 'controller', 'Presence')
        polyglot.runForever()

    except (KeyboardInterrupt, SystemExit):
        udi_interface.Interface([]).stop()
        sys.exit(0)
