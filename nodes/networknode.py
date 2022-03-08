import subprocess as sp
import udi_interface

LOGGER = udi_interface.LOGGER
custom = udi_interface.Custom


class PingHelper(object):

    def __init__(self, ip, timeout):
        self.host = ip
        self.timeout = str(timeout)

    def ping(self):
        try:
            LOGGER.debug(f'Trying {self.host} with timeout {self.timeout}')
            response = sp.call(['/sbin/ping', '-c1', '-W' + self.timeout, self.host], shell=False)
            LOGGER.debug(f'Ping response {response}')

            if response == 0:
                return response
            else:
                return None
        except Exception as e:
            LOGGER.debug(f'Error in Ping {e}')
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

            onnet = PingHelper(ip=self.ip, timeout=15)
            result = onnet.ping()

            if result is not None:
                LOGGER.info('Network ' + self.ip + ': On Network')
                self.setOnNetwork(5)
            elif self.strength > 1:
                self.setOnNetwork(self.strength - 1)
                LOGGER.info('Network ' + self.ip + ': In Fault')
            elif self.strength == 1:
                LOGGER.info('Network ' + self.ip + ': Out of Network')
                self.setOffNetwork()
            else:
                LOGGER.warning(f'Invalid response received from Ping: {result}')
        return

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
