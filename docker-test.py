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
    h1 = net.addHost( 'h1', cls=Docker, ip='10.0.1.11/24', dimage="ubuntu:trusty" )
    h2 = net.addHost( 'h2', cls=Docker, ip='10.0.1.12/24', dimage="ubuntu:trusty" )
    h3 = net.addHost( 'h3', cls=Docker, ip='10.0.1.13/24', dimage="ubuntu:trusty" )
    h4 = net.addHost( 'h4', cls=Docker, ip='10.0.1.14/24', dimage="ubuntu:trusty" )
    info( '*** Adding switch\n' )
    s1 = net.addSwitch( 's1')
    s2 = net.addSwitch( 's2')
    s3 = net.addSwitch( 's3')
    info( '*** Creating links\n' )
    l1 = net.addLink( s1, s2)
    l2 = net.addLink( s2, s3)
    #ovsl3 = net.addLink( s3, s1,bw=200,cls=TCLink)
    l3 = net.addLink( h1, s1)
    l4 = net.addLink( h2, s2)
    l5 = net.addLink( h3, s2)
    l6 = net.addLink( h4, s3)
    info( '*** Starting network\n')
    net.start()
    set_vlan_access(l3,10)
    set_vlan_access(l4,10)
    set_vlan_trunk(l1,10)
    set_vlan_trunk(l2,20)
    set_vlan_access(l5,20)
    set_vlan_access(l6,20)
    #set_vlan_trunk(ovsl3,30)
    #run('ifconfig s1 10.0.1.1 netmask 255.255.255.0 up')
    #run('ifconfig s2 10.0.2.1 netmask 255.255.255.0 up')
    #run('ifconfig s3 10.0.3.1 netmask 255.255.255.0 up')
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
    testRing()





