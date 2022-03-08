import array
import fcntl
import struct

import pyblue as bt
import udi_interface

LOGGER = udi_interface.LOGGER
custom = udi_interface.Custom

'''
class BlueHelper(object):

    def __init__(self, addr):
        # Initializes bluetooth object
        self.addr = addr

        self.hci_sock = bt.hci_open_dev()
        self.hci_fd = self.hci_sock.fileno()
        self.bt_sock = bt.BluetoothSocket(bluetooth.L2CAP)
        self.bt_sock.settimeout(10)
        self.connected = False
        self.cmd_pkt = None

    def prepare_command(self):
        # Creates the command
        reqstr = struct.pack(
            "6sB17s", bt.str2ba(self.addr), bt.ACL_LINK, bytes("\0", 'utf-8') * 17)
        request = array.array("b", reqstr)
        handle = fcntl.ioctl(self.hci_fd, bt.HCIGETCONNINFO, request, 1)
        handle = struct.unpack("8xH14x", request.tobytes())[0]
        self.cmd_pkt = struct.pack('H', handle)

    def connect(self):
        # Connects to the bluetooth device
        self.bt_sock.connect_ex((self.addr, 1))
        self.connected = True

    def get_rssi(self):
        # Gets the RSSI value
        try:
            # Only do connection if not already connected
            if not self.connected:
                self.connect()
            if self.cmd_pkt is None:
                self.prepare_command()
            # Send command to request RSSI
            rssi = bt.hci_send_req(
                self.hci_sock, bt.OGF_STATUS_PARAM,
                bt.OCF_READ_RSSI, bt.EVT_CMD_COMPLETE, 4, self.cmd_pkt)
            rssi = struct.unpack('b', rssi[3:4])[0]
            return rssi
        except IOError as ioerr:
            # Happens if connection fails
            # LOGGER.debug("I/O error: {0}".format(ioerr))
            self.connected = False
            return None


class BluetoothNode(udi_interface.Node):
    def __init__(self, controller, primary, address, name):
        super(BluetoothNode, self).__init__(controller, primary, address, name)
        self.blueid = ':'.join(self.address[i:i + 2] for i in range(0, len(self.address), 2)).upper()
        self.scan = 1
        self.proximity = 0

    def start(self):
        self.setOn('DON')

    def update(self):
        if self.scan:
            btnode = BlueHelper(addr=self.blueid)
            result = btnode.get_rssi()
            if result is not None:
                LOGGER.debug('Bluetooth ' + self.blueid + ': In range. RSSI: ' + str(result))
                if result >= 0:
                    self.setInRange(5)
                elif 0 > result >= -5:
                    self.setInRange(4)
                elif -5 > result >= -15:
                    self.setInRange(3)
                elif -15 > result >= -35:
                    self.setInRange(2)
                elif result < -35:
                    self.setInRange(1)
            elif self.proximity > 1:
                self.setInRange(self.proximity - 1)
                LOGGER.debug('Bluetooth ' + self.blueid + ': In Fault')
            elif self.proximity == 1:
                LOGGER.debug('Bluetooth ' + self.blueid + ': Out of range')
                self.setOutRange()

    def setInRange(self, prox):
        self.setDriver('ST', 1)
        self.proximity = prox
        self.setDriver('GV0', self.proximity)

    def setOutRange(self):
        self.setDriver('ST', 0)
        self.proximity = 0
        self.setDriver('GV0', self.proximity)

    def setOn(self, command):
        self.setOutRange()
        self.setDriver('GV1', 1)
        self.scan = 1

    def setOff(self, command):
        self.setOutRange()
        self.setDriver('GV1', 0)
        self.scan = 0

    def query(self):
        self.reportDrivers()

    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'GV0', 'value': 0, 'uom': 56},
        {'driver': 'GV1', 'value': 1, 'uom': 2}
    ]

    id = 'bluetooth_node'

    commands = {
        'DON': setOn, 'DOF': setOff
    }
'''