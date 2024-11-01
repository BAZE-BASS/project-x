import csv
import time
from time import sleep
from threading import Thread
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import RemoteController
from mininet.log import setLogLevel, info

def log_traffic(net, interval=2, filename='traffic_data.csv'):
    """Logs TX and RX bytes for each host in the network at specified intervals."""
    with open(filename, mode='w') as f:
        writer = csv.writer(f)
        writer.writerow(["time", "host", "tx_bytes", "rx_bytes"])
        
        try:
            while True:
                for host in net.hosts:
                    tx_bytes = host.cmd('ifconfig').split('TX bytes:')[1].split()[0]
                    rx_bytes = host.cmd('ifconfig').split('RX bytes:')[1].split()[0]
                    writer.writerow([time.time(), host.name, tx_bytes, rx_bytes])
                sleep(interval)
        except KeyboardInterrupt:
            info("Stopping traffic logging\n")

def createMyTopo():
    """Sets up the Mininet topology and starts logging traffic."""
    net = Mininet(controller=RemoteController)
    cA = net.addController('cA', controller=RemoteController, ip="127.0.0.1", port=6643)
    cB = net.addController('cB', controller=RemoteController, ip="127.0.0.1", port=6653)

    # Define hosts and switches setup here

    net.build()
    cA.start()
    cB.start()

    # Start data logging in a separate thread
    log_thread = Thread(target=log_traffic, args=(net,))
    log_thread.start()

    CLI(net)
    net.stop()

    # Ensure logging stops when the network stops
    log_thread.join()

if __name__ == '__main__':
    setLogLevel('info')
    createMyTopo()
