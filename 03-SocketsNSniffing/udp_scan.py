import socket
import os
import struct
from ctypes import *
from netaddr import IPNetwork, IPAddress
import time
import threading
#import get_ip  #Use when IPv6 is supported

verbose = False


def vprint(verbose_string, lverbose=False):
    global verbose
    if lverbose or verbose:
        if lverbose is True:
            icon = '*'
        else:
            icon = lverbose
        print('[{}] {}'.format(icon, verbose_string))


def get_Host_IP():
    # Can't handle IPv6 yet...set host_ip to none so IPv4 discovery is preferred
    host_ip = None  # get_ip.get_local_addr()
    if not host_ip:
        try:
            host_name = socket.gethostname()
            host_ip = socket.gethostbyname(host_name)

            # If gethostbyname method didn't work as expected
            if host_ip == '127.0.0.1' or host_ip == 'localhost':
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # Try a connection attempt to get default route interface IP
                try:
                    # Connect to unreachable IP & force default route
                    s.connect(('10.255.255.255', 1))
                    host_ip = s.getsockname()[0]
                except Exception:
                    raise
                finally:
                    s.close()
        except Exception as egip:
            print('Unable to get IP: {}'.format(egip))
    return host_ip


class IP(Structure):
    _fields_ = [
        ('ihl', c_ubyte, 4),
        ('version', c_ubyte, 4),
        ('tos', c_ubyte),
        ('len', c_ushort),
        ('id', c_ushort),
        ('offset', c_ushort),
        ('ttl', c_ubyte),
        ('protocol_num', c_ubyte),
        ('sum', c_ushort),
        ('src', c_uint32),
        ('dst', c_uint32)
    ]

    def __new__(self, socket_buffer=None):
        return self.from_buffer_copy(socket_buffer)

    def __init__(self, socket_buffer=None):
        self.protocol_map = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}

        # Human readable IP addresses...
        self.src_address = socket.inet_ntoa(struct.pack('@I', self.src))
        self.dst_address = socket.inet_ntoa(struct.pack('@I', self.dst))

        try:
            self.protocol = self.protocol_map[self.protocol_num]
        except Exception as ei:
            self.protocol = str(self.protocol_num)


class ICMP(Structure):
    _fields_ = [
        ('type', c_ubyte),
        ('code', c_ubyte),
        ('checksum', c_ushort),
        ('unused', c_ushort),
        ('next_hop_mtu', c_ushort)
    ]

    def __new__(self, socket_buffer):
        return self.from_buffer_copy(socket_buffer)

    def __init__(self, socket_buffer):
        pass


def set_af_protocol(host=get_Host_IP()):
    if ':' in host:
        ip_type = socket.IPPROTO_IPV6
        sock_af = socket.AF_INET6
        if os.name == 'nt':
            socket_protocol = socket.IPPROTO_IPV6
        else:
            socket_protocol = socket.IPPROTO_ICMPV6
    elif '.' in host:
        ip_type = socket.IPPROTO_IP
        sock_af = socket.AF_INET
        if os.name == 'nt':
            socket_protocol = socket.IPPROTO_IP
        else:
            socket_protocol = socket.IPPROTO_ICMP
    else:
        return None
    return sock_af, socket_protocol, ip_type


def udp_sender(subnet, message):
    time.sleep(3)
    if not isinstance(message, bytes):
        message = message.encode()
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(subnet)
    for ip in IPNetwork(subnet):
        try:
            last_octet = str(ip).split('.')[3]
            if last_octet in ('0', '255'):
                continue
            sender.sendto(message, ('{}'.format(ip), 65212))
        except Exception as e:
            raise


def main():
    host = get_Host_IP()
    subnet = '.'.join(host.split('.')[:3]) + '.0/24'

    magic_strings = b'Python'
    t = threading.Thread(target=udp_sender, args=(subnet, magic_strings))
    t.start()
    sock_af, socket_protocol, ip_type = set_af_protocol(host)

    # Turn on promiscuous mode for Windows
    with socket.socket(
            sock_af,
            socket.SOCK_RAW,
            socket_protocol) as sniffer:
        # breakpoint()
        sniffer.bind((host, 0))

        # Include IP headers
        sniffer.setsockopt(ip_type, socket.IP_HDRINCL, 1)

        if os.name == 'nt':
            sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
        try:
            while True:
                raw_buffer = sniffer.recvfrom(65565)[0]
                # breakpoint()
                ip_header = IP(raw_buffer[:20])
                # print('Protocol: {} {} -> {}'.format(
                #     ip_header.protocol,
                #     ip_header.src_address,
                #     ip_header.dst_address))
                if ip_header.protocol == 'ICMP':
                    offset = ip_header.ihl * 4
                    buf = raw_buffer[offset:offset + sizeof(ICMP)]
                    icmp_header = ICMP(buf)
                    src_address = ip_header.src_address
                    # print('ICMP -> Type: {} Code: {}'.format(
                    #     icmp_header.type,
                    #     icmp_header.code))
                    if icmp_header.code == 3 and icmp_header.type == 3:
                        if IPAddress(src_address) in IPNetwork(subnet):
                            sindex = len(raw_buffer) - len(magic_strings)
                            if raw_buffer[sindex:] == magic_strings:
                                print('Host Up: {}'.format(src_address))
        except KeyboardInterrupt:
            # Turn off promiscuous mode for Windows
            if os.name == 'nt':
                sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)


if __name__ == '__main__':
    main()
