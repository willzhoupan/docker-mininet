#!/usr/bin/python
"""
Example topology with two containers (d1, d2),
two switches, and one controller:

          - (c)-
         |      |
(d1) - (s1) - (s2) - (d2)
"""
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.link import OVSLink
from mininet.topo import Topo
from mininet.node import Controller
from dockernode import Docker
import subprocess

def run(cmd):
    command = 'sudo ' + cmd
    ret = subprocess.call(command, shell=True)
    #logger.info('[{1}] {0}'.format(' '.join(command), ret))
    return ret
def set_link_bw(link, bw1,bw2):
    cmd_list = []
    #set rates intf1->intf2
    cmd_list.append('ovs-vsctl set interface '+link.intf2.name+' ingress_policing_rate='+str(bw1))
    cmd_list.append('ovs-vsctl set interface '+link.intf2.name+' ingress_policing_burst='+str(int(bw1*0.1)))
    
    #set rates intf2->intf1
    cmd_list.append('ovs-vsctl set interface '+link.intf1.name+' ingress_policing_rate='+str(bw2))
    cmd_list.append('ovs-vsctl set interface '+link.intf1.name+' ingress_policing_burst='+str(int(bw2*0.1)))
   
    for cmd in cmd_list:
        #print(cmd)
        ret = run(cmd)
        if ret != 0:
           print('**Error: Edge->('+link.intf1.name+','+link.intf2.name+') set bw failed!')
           return False

def set_vlan_trunk(link,vlan):
    cmd_list = []
    cmd_list.append('ovs-vsctl set port '+link.intf1.name+' vlan_mode=trunk tag='+str(vlan))
    cmd_list.append('ovs-vsctl set port '+link.intf2.name+' vlan_mode=trunk tag='+str(vlan))
    for cmd in cmd_list:
        #print(cmd)
        ret = run(cmd)
        if ret != 0:
           print('**Error: Edge->('+s_node+','+e_node+') created failed!')
           #check_ovs(ovslist)
           return False  

def set_vlan_access(link,vlan):
    cmd_list = []
    cmd_list.append('ovs-vsctl set port '+link.intf2.name+' vlan_mode=access tag='+str(vlan))
    for cmd in cmd_list:
        #print(cmd)
        ret = run(cmd)
        if ret != 0:
           print('**Error: Edge->('+s_node+','+e_node+') created failed!')
           #check_ovs(ovslist)
           return False
  
#tell user choose to delete it or rename it 
def check_docker(dockerlist):
    #delete existing docker in dockerlist
    for docker in dockerlist:
        #1.stop the docker => 2.remove it
        #find running dockers with same name as docker
        ret = subprocess.check_output("sudo docker ps --filter status=running |grep "+docker+" |awk '{print$1}'", shell=True)
        ret_str = str(ret)
        running_dockers = ret_str.split('\n')#return the ids of running dockers
        if running_dockers[-1] == '':
           running_dockers = running_dockers[:-1]
        #stop running dockers
        for item in running_dockers:
            run('docker container stop '+item)
        #find exited dockers with same name as docker 
        ret = subprocess.check_output("sudo docker ps -a |grep "+docker+" |awk '{print$1}'", shell=True)
        ret_str = str(ret)
        exited_dockers = ret_str.split('\n')#return the ids of running dockers
        if exited_dockers[-1] == '':
           exited_dockers = exited_dockers[:-1]
        #remove exited dockers with same name as docker
        for item in exited_dockers:
            run('docker container rm '+item)

class DockerTopo(Topo):
    "Single switch connected to n hosts."
    def __init__(self, n=2, **opts):
        # Initialize topology and default options
        Topo.__init__(self, **opts)
        switch = self.addSwitch('s1')
        # Python's range(N) generates 0..N-1
        for h in range(n):
            #info('*** Adding host h%s\n' % (h + 1))
            host = self.addHost('h%s' % (h + 1), cls=Docker, ip='10.0.0.%s'% (h + 1), dimage="daml:latest")
            #host = self.addHost('h%s' % (h + 1))
            #info('*** Adding link\n')
            self.addLink(host,switch,delay='50ms',bw=100,cls=TCLink)

def simpleTest():
    "Create and test a simple network"
    topo = DockerTopo(n=2)
    net = Mininet(topo) 
    info('*** Starting network\n')
    net.start()
    print "Testing network connectivity"
    net.pingAll()
    info('*** Running CLI\n')
    CLI(net)
    info('*** Stopping network')
    net.stop()

def testRing():
    "Create ring topology."
    info( '*** Deleting existing docker named mn.h*\n' )
    docker_list = []
    docker_list.append('mn.h')
    check_docker(docker_list)
    net = Mininet( controller=Controller )
    info( '*** Adding controller\n' )
    net.addController( 'c0' )
    info( '*** Adding hosts\n' )
    h1 = net.addHost( 'h1', cls=Docker, ip='10.0.0.11/24', dimage="willzhoupan/daml:v-stsp" )
    h2 = net.addHost( 'h2', cls=Docker, ip='10.0.0.12/24', dimage="willzhoupan/daml:v-stsp" )
    h3 = net.addHost( 'h3', cls=Docker, ip='10.0.0.13/24', dimage="willzhoupan/daml:v-stsp" )
    h4 = net.addHost( 'h4', cls=Docker, ip='10.0.0.14/24', dimage="willzhoupan/daml:v-stsp" )
    info( '*** Adding switch\n' )
    s1 = net.addSwitch( 's1')
    s2 = net.addSwitch( 's2')
    info( '*** Creating links\n' )
    l1 = net.addLink( h1, s1)
    l2 = net.addLink( h2, s1)
    l3 = net.addLink( h3, s2)
    l4 = net.addLink( h4, s2)
    l5 = net.addLink( s1, s2,bw=20,cls=TCLink)
    info( '*** Starting network\n')
    net.start()
    #run('ifconfig s1 10.0.0.1 netmask 255.255.255.0 up')
    net.pingAll()
    info( '*** Running CLI\n' )
    CLI( net )
    info( '*** Stopping network' )
    net.stop()

def testCoordinator():
    "Create ring topology."
    info( '*** Deleting existing docker named mn.h*\n' )
    docker_list = []
    docker_list.append('mn.h')
    check_docker(docker_list)
    net = Mininet( controller=Controller )
    info( '*** Adding controller\n' )
    net.addController( 'c0' )
    info( '*** Adding hosts\n' )
    h0 = net.addHost( 'h0', cls=Docker, ip='10.0.0.10/24', dimage="willzhoupan/daml:v-csp" )
    h1 = net.addHost( 'h1', cls=Docker, ip='10.0.0.11/24', dimage="willzhoupan/daml:v-csp" )
    h2 = net.addHost( 'h2', cls=Docker, ip='10.0.0.12/24', dimage="willzhoupan/daml:v-csp" )
    h3 = net.addHost( 'h3', cls=Docker, ip='10.0.0.13/24', dimage="willzhoupan/daml:v-csp" )
    h4 = net.addHost( 'h4', cls=Docker, ip='10.0.0.14/24', dimage="willzhoupan/daml:v-csp" )
    info( '*** Adding switch\n' )
    s1 = net.addSwitch( 's1')
    s2 = net.addSwitch( 's2')
    info( '*** Creating links\n' )
    l0 = net.addLink( h0, s1)
    l1 = net.addLink( h1, s1)
    l2 = net.addLink( h2, s1)
    l3 = net.addLink( h3, s2)
    l4 = net.addLink( h4, s2)
    l5 = net.addLink( s1, s2,bw=20,cls=TCLink)
    info( '*** Starting network\n')
    net.start()
    #run('ifconfig s1 10.0.0.1 netmask 255.255.255.0 up')
    net.pingAll()
    info( '*** Running CLI\n' )
    CLI( net )
    info( '*** Stopping network' )
    net.stop()

def test():
    "Create an empty network and add nodes to it."
    net = Mininet( controller=Controller )
    info( '*** Adding controller\n' )
    net.addController( 'c0' )
    info( '*** Adding hosts\n' )
    h1 = net.addHost( 'h1')
    h2 = net.addHost( 'h2', cls=Docker, ip='10.0.0.2', dimage="ubuntu:trusty" )
    info( '*** Adding switch\n' )
    s1 = net.addSwitch( 's1' )
    s2 = net.addSwitch( 's2' )
    info( '*** Creating links\n' )
    net.addLink( s1, s2 )
    net.addLink( s1, h1 )
    net.addLink( h2, s2 )
    info( '*** Starting network\n')
    net.start()
    info( '*** Running CLI\n' )
    CLI( net )
    info( '*** Stopping network' )
    net.stop()

if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    #testRing()
    testCoordinator()





