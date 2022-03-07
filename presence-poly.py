#!/usr/bin/env python3
import udi_interface
import sys
import time
import bluetooth as bt
import struct
import array
import fcntl
import os

LOGGER = udi_interface.LOGGER
Custom = udi_interface.Custom


class Controller(udi_interface.Node):
    id = 'presence_controller'

    def __init__(self, polyglot, parent, address, name):
        super(Controller, self).__init__(polyglot, parent, address, name)
        self.name = 'Presence Controller'
        self.firstRun = True
        self.poly = polyglot
        self.name = name
        self.address = address
        self.primary = parent
        self.configured = False

        self.Parameters = Custom(polyglot, 'customparams')
        self.Notices = Custom(polyglot, 'notices')

        # self.poly.subscribe(self.poly.CONFIG, self.configHandler)
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.check_params)
        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.POLL, self.poll)
        self.poly.subscribe(self.poly.LOGLEVEL, self.handleLevelChange)
        self.poly.subscribe(self.poly.CONFIG, self.ns_config)

        self.poly.subscribe(self.poly.STOP, self.stop_handler)
        # self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)

        self.poly.ready()
        self.poly.addNode(self)

    def start(self):
        LOGGER.info('Presence Controller started.')
        # self.discover()
        self.setDriver('ST', 1)

    def poll(self, polltype):

        if not self.configured:
            return
        if 'shortPoll' in polltype:
            self.shortPoll()

    def shortPoll(self):
        # This is where the updates to each node happen

        for node_address in self.poly.getNodes():
            node = self.poly.getNode(node_address)

            LOGGER.debug(f'Polling, node={node}, node.address={node.address} node.name={node.name}')
            node.update()

        if self.firstRun:
            self.query()
            self.firstRun = False

    def longPoll(self):
        # Not used
        pass

    def query(self):
        for node in self.poly.nodes():
            node.reportDrivers()

    def discover(self):
        # self.Parameters.load(parameters)
        # Discover nodes and add them by type
        LOGGER.debug(f'Parameters: {self.Parameters}')
        for key, val in self.Parameters.items():
            LOGGER.debug(key + " => " + val)
            if val.find(':') != -1:
                blueid = val.replace(':', '').lower()
                # self.poly.addNode(BluetoothNode(self, self.address, blueid, key))
            elif val.find('.') != -1:
                netip = val.replace('.', '')
                self.poly.addNode(NetworkNode(self.poly, self.address, netip, val, key))

        self.configured = True

    def update(self):
        pass

    def ns_config(self, data):
        LOGGER.debug(f'NODESERVER Config: {data.get.shortPoll}')

    def handleLevelChange(self, level):
        LOGGER.info('New log level: {}'.format(level))

    def delete(self):
        LOGGER.info('Deleted')

    def stop_handler(self):
        self.setDriver('ST', 0)
        LOGGER.debug('Presence Controller stopped.')

    def check_params(self, config):
        self.Parameters.load(config)
        self.discover()
        # Remove all existing notices
        self.Notices.clear()

    def update_profile(self, command):
        LOGGER.info('update_profile:')
        st = self.poly.installprofile()
        return st

    commands = {
        'DISCOVER': discover,
        'UPDATE_PROFILE': update_profile,
    }
    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2}
    ]


'''
class BlueHelper(object):

    def __init__(self, addr):
        # Initializes bluetooth object
        self.addr = addr

        self.hci_sock = bt.hci_open_dev()
        self.hci_fd = self.hci_sock.fileno()
        self.bt_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
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


class PingHelper(object):

    def __init__(self, ip, timeout):
        self.ip = ip
        self.timeout = timeout

    def ping(self):
        try:
            response = os.system("ping -c 1 -W " + str(self.timeout - 1) + " " + self.ip)
            if response == 0:
                return response
            else:
                return None
        except:
            # Capture any exception
            return None


class NetworkNode(udi_interface.Node):

    def __init__(self, controller, primary, address, ipaddress, name):
        super(NetworkNode, self).__init__(controller, primary, address, name)
        self.ip = ipaddress
        self.scan = 1
        self.strength = 0

    def start(self):
        self.setOn('DON')

    def update(self):
        if self.scan:
            # onnet = PingHelper(ip=self.ip, timeout=self.primary.polyConfig['shortPoll'])
            onnet = PingHelper(ip=self.ip, timeout=15)
            result = onnet.ping()
            if result is not None:
                LOGGER.debug('Network ' + self.ip + ': On Network')
                self.setOnNetwork(5)
            elif self.strength > 1:
                self.setOnNetwork(self.strength - 1)
                LOGGER.debug('Network ' + self.ip + ': In Fault')
            elif self.strength == 1:
                LOGGER.debug('Network ' + self.ip + ': Out of Network')
                self.setOffNetwork()

    def setOnNetwork(self, strength):
        self.setDriver('ST', 1)
        self.strength = strength
        self.setDriver('GV0', self.strength)

    def setOffNetwork(self):
        self.setDriver('ST', 0)
        self.strength = 0
        self.setDriver('GV0', self.strength)

    def setOn(self, command):
        self.setOffNetwork()
        self.setDriver('GV1', 1)
        self.scan = 1

    def setOff(self, command):
        self.setOffNetwork()
        self.setDriver('GV1', 0)
        self.scan = 0

    def query(self):
        self.reportDrivers()

    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'GV0', 'value': 0, 'uom': 56},
        {'driver': 'GV1', 'value': 1, 'uom': 2}
    ]

    id = 'network_node'

    commands = {
        'DON': setOn, 'DOF': setOff
    }


if __name__ == "__main__":
    try:
        polyglot = udi_interface.Interface([])
        polyglot.start()
        control = Controller(polyglot, 'controller', 'controller', 'presence')
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
