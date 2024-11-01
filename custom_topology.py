from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def create_network():
    net = Mininet(controller=RemoteController)
    c0 = net.addController('c0', ip='127.0.0.1', port=6653)

    # Add switches and hosts
    s1 = net.addSwitch('s1')
    h1 = net.addHost('h1')
    h2 = net.addHost('h2')

    # Set up links
    net.addLink(h1, s1)
    net.addLink(h2, s1)

    net.build()
    c0.start()
    s1.start([c0])

    # Start CLI for testing
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_network()

