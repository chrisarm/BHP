#!/usr/bin/env python3
import sys
import socket
import threading
import ipaddress
import struct
import argparse

verbose = False
deffmt = 'C1'


def vprint(verbose_string):
    global verbose
    if verbose:
        print('[*] {}'.format(verbose_string))


def request_handler(buff):
    # Packet Modifications here!
    return buff


def response_handler(buff):
    # More packet modifications here!
    return buff


def send_msg(sock, buff):
    if not isinstance(buff, bytes):
        buff = buff.encode()
    sock.send(buff)


def recv_msg(sock):
    '''Handle receiving messages along with the message length'''
    # Read message length and unpack it into an integer
    data = b''
    while True:
        raw_msg = sock.recv(4096)
        data += raw_msg
        if len(raw_msg) < 4096:
            break
    # Return decoded text rather than bytes by default
    return data.decode()


def recvall(sock, n):
    '''Helper function to recv n bytes or return None if EOF is hit'''
    data = b''
    try:
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
    except ConnectionResetError as cre:
        return None
    return data


def validate_ip(address):
    try:
        address = ipaddress.ip_address(address)
        return address
    except Exception as ev:
        vprint('Invalid IP address provided.\n{e}'.format(e=ev))
        return None


def hexdump(src, length=16):
    result = []
    digits = 4 if isinstance(src, str) else 2
    for i in range(0, len(src), length):
        s = src[i:i + length]
        hexa = b' '.join([b'%0*X' % (digits, ord(x)) for x in s])
        textitems = [x.encode() if 0x20 <= ord(x) < 0x7F else b'.' for x in s]
        text = b''.join(textitems)
        result.append(b'%04X   %-*s   %s' % (
            i,
            length * (digits + 1),
            hexa,
            text))
    result = b'\n'.join(result)
    print(result.decode())


def proxy_handler(client_socket, rhost, rport, receive_first):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as remote_socket:
        remote_socket.connect((rhost, rport))
        vprint('Connected to remote system {ip}:{port}'.format(
            ip=rhost,
            port=rport))

        if receive_first:
            remote_buffer = recv_msg(remote_socket)
            hexdump(remote_buffer)

            remote_buffer = response_handler(remote_buffer)
            lenlbuf = len(remote_buffer)

            if lenlbuf:
                vprint('Sending {len} bytes to lhost.'.format(len=lenlbuf))
                send_msg(client_socket, remote_buffer)

        while True:
            local_buffer = recv_msg(client_socket)
            lenrbuf = len(local_buffer)

            if lenrbuf:
                vprint('Received {len} bytes from lhost'.format(len=lenrbuf))
                hexdump(local_buffer)

                local_buffer = request_handler(local_buffer)
                send_msg(remote_socket, local_buffer)
                vprint('Forwarded to remote client')

            remote_buffer = recv_msg(remote_socket)
            lenlbuf = len(remote_buffer)

            if lenlbuf:
                vprint('Received {len} bytes from remote'.format(len=lenlbuf))
                hexdump(remote_buffer)

                remote_buffer = response_handler(remote_buffer)
                send_msg(client_socket, remote_buffer)
                vprint('Sent to localhost')

            if not lenlbuf or not lenrbuf:
                client_socket.close()
                remote_socket.close()
                print('No more data. Closing proxy connections')
                break


def server_loop(lhost, lport, rhost, rport, recv_1st):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        try:
            server.bind((lhost, lport))
            vprint('Listening on on {host}:{port}'.format(
                host=lhost,
                port=lport))
            server.listen(5)
        except Exception as esl:
            vprint('Error: {}'.format(esl))
            print('Failed to listen on {host}:{port}'.format(
                host=lhost,
                port=lport))
            sys.exit(1)

        while True:
            try:
                client_socket, addr = server.accept()

                # print out the local connection information
                print('Received incoming connection from {ip}:{port}'.format(
                    ip=addr[0],
                    port=addr[1]))

                # start a thread to talk to the remote host
                proxy_thread = threading.Thread(
                    target=proxy_handler,
                    args=(client_socket, rhost, rport, recv_1st))
                proxy_thread.start()
            except Exception as esl2:
                vprint('Problem proxying new connection.\n{error}'.format(
                    error=esl2))


def main(lhost, lport, rhost, rport, receive_first):
    server_loop(lhost, lport, rhost, rport, receive_first)


if __name__ == '__main__':
    a_parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            '''
TCP Proxy Tool.
            '''))
    a_parser.add_argument(
        '-l',
        '--lhost',
        help='Address used to listen: -l 127.0.0.1')
    a_parser.add_argument(
        '-p',
        '--lport',
        type=int,
        help='Target address or hostname: -p 7890')
    a_parser.add_argument(
        '-r',
        '--rhost',
        help='IP of client listening for forwarded data stream: -r <rhost>')
    a_parser.add_argument(
        '-q',
        '--rport',
        type=int,
        help='Port of remote client listeining for data stream: -q <rport>')
    a_parser.add_argument(
        '-1',
        '--recvfirst',
        action='store_true',
        help='Recive data first: [-1] (Flag #1 = True, nothing = False.)')
    a_parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Prints more messages about status.')
    a_parser.add_argument(
        '-f',
        '--format',
        default='',
        help='Default network message format.')
    proxy_args = a_parser.parse_args()

    # Go through each argument from the command line input
    if proxy_args.verbose:
        verbose = proxy_args.verbose

    if proxy_args.recvfirst:
        receive_first = True
    else:
        receive_first = False

    if proxy_args.format:
        deffmt = proxy_args.format
    else:
        deffmt = ''

    lhost = proxy_args.lhost
    lport = proxy_args.lport
    rhost = proxy_args.rhost
    rport = proxy_args.rport
    main(lhost, lport, rhost, rport, receive_first)
