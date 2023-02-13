import udi_interface
from nodes import NetworkNode

LOGGER = udi_interface.LOGGER
Custom = udi_interface.Custom


class Controller(udi_interface.Node):
    id = 'presence'

    def __init__(self, polyglot, parent, address, name):
        super(Controller, self).__init__(polyglot, parent, address, name)
        self.poly = polyglot
        self.name = name
        self.address = address
        self.primary = parent
        self.configured = False

        self.Parameters = Custom(polyglot, 'customparams')
        self.Notices = Custom(polyglot, 'notices')

        self.poly.subscribe(self.poly.CONFIG, self.configHandler)
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.check_params)
        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.POLL, self.poll)
        self.poly.subscribe(self.poly.LOGLEVEL, self.handleLevelChange)

        self.poly.subscribe(self.poly.STOP, self.stop_handler)
        # self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)

        self.poly.ready()
        self.poly.addNode(self)

    def start(self):
        LOGGER.info('Presence Controller started.')
        self.query()
        self.setDriver('ST', 1)

        self.poll('shortPoll')

    def poll(self, polltype):

        if not self.configured:
            return
        if 'shortPoll' in polltype:
            self.short_Poll()

    def short_Poll(self):
        # This is where the updates to each node happen
        for node_address in self.poly.getNodes():
            node = self.poly.getNode(node_address)
            LOGGER.debug(f'Node name: {node.name}')
            if node.name != 'Presence':
                LOGGER.debug(f'Polling, node.address={node.address} node.name={node.name}')
                node.update()

    def longPoll(self):
        # Not used
        pass

    def query(self):
        for node in self.poly.nodes():
            node.reportDrivers()

    def check_params(self, config):
        self.Parameters.load(config)
        LOGGER.debug(f'Loading Parameters: {self.Parameters}')
        # Remove all existing notices
        self.discover()

        self.Notices.clear()

    def discover(self):
        # self.Parameters.load(parameters)
        # Discover nodes and add them by type
        LOGGER.debug(f'Parameters: {self.Parameters}')
        for key, val in self.Parameters.items():
            LOGGER.debug(key + " => " + val + str(val.find(".")))
            if val.find(':') != -1:
                blueid = val.replace(':', '').lower()
                # self.poly.addNode(BluetoothNode(self, self.address, blueid, key))
            elif val.find('.') != -1:
                netip = val.replace('.', '')
                LOGGER.debug(f'Adding node: {netip}: {key} - {val}')
                self.poly.addNode(NetworkNode(self.poly, self.address, netip, val, key))
                LOGGER.debug(f'Added node {netip} {val} {key}')

        self.configured = True

    def update(self):
        pass

    def configHandler(self, data):
        LOGGER.debug(f"NODESERVER Config: {data['shortPoll']}")
        self.shortpoll_time = data['shortPoll']

    def handleLevelChange(self, level):
        LOGGER.info('New log level: {}'.format(level))

    def delete(self):
        LOGGER.info('Deleted')

    def stop_handler(self):
        self.setDriver('ST', 0)
        LOGGER.debug('Presence Controller stopped.')
        self.poly.stop()

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

