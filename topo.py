#!/usr/bin/python3
from mn_wifi.net import Mininet_wifi
from mn_wifi.cli import CLI
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.log import setLogLevel
from mininet.link import TCLink

def topology():
    net = Mininet_wifi(controller=RemoteController, link=TCLink, switch=OVSKernelSwitch)

    print("*** Creating Nodes ***")
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

    # Βάζουμε 2 APs
    ap1 = net.addAccessPoint('ap1', ssid='vanet-ap1', mode='g', channel='1', 
                             protocols='OpenFlow13', position='30,50,0', range=50)
    ap2 = net.addAccessPoint('ap2', ssid='vanet-ap2', mode='g', channel='6', 
                             protocols='OpenFlow13', position='70,50,0', range=50)

    server = net.addHost('server', ip='10.0.0.100/8', position='50,90,0')
    s1 = net.addSwitch('s1', protocols='OpenFlow13')

    print("*** Creating Vehicles ***")
    # Τα αυτοκίνητα είναι ΣΤΑΘΕΡΑ μέσα στην εμβέλεια του AP1
    car1 = net.addStation('car1', ip='10.0.0.1/8', position='25,50,0')
    car2 = net.addStation('car2', ip='10.0.0.2/8', position='35,50,0')

    print("*** Configuring WiFi Nodes ***")
    net.configureWifiNodes()

    print("*** Creating Links ***")
    net.addLink(server, s1, bw=100)
    net.addLink(s1, ap1, bw=20) 
    net.addLink(s1, ap2, bw=20)

    # Ενεργοποίηση της γραφικής απεικόνισης του Mininet-WiFi
    print("*** Plotting Graph ***")
    net.plotGraph(max_x=100, max_y=100)

    print("*** Starting Network ***")
    net.build()
    c0.start()
    s1.start([c0])
    ap1.start([c0])
    ap2.start([c0])

    print("*** Running CLI ***")
    CLI(net)

    print("*** Stopping Network ***")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()
