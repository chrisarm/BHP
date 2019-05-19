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
        vprint('Server: {pld}'.format(pld=mail_packet))


sniff(
    filter='tcp port 443',
    prn=packet_callback,
    count=20,
    store=0
    )
