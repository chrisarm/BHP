from sys import exit, stdin
from pathlib import Path
import socket
import ipaddress
import argparse
import threading
import subprocess
import struct
import time

verbose = False


def vprint(verbose_string):
    global verbose
    if verbose:
        print('[*] {}'.format(verbose_string))


def send_msg(sock, msg, frmt=''):
    '''Handle sending messages along with the message length'''
    # Prefix each message with a 8-byte length (network byte order)
    if not isinstance(msg, bytes):
        msg = msg.encode()

    if frmt == 'C7':
        msg = frmt.encode() + struct.pack('>Q', len(msg)) + msg
    sock.sendall(msg)


def recv_msg(sock, frmt=''):
    '''Handle receiving messages along with the message length'''
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 10)
    if not raw_msglen:
        return None
    # Handle custom messages from this server/client combo
    elif 'C7'.encode() in raw_msglen:
        msglen = struct.unpack('>Q', raw_msglen[2:10])[0]
        # Read the message data
        data = recvall(sock, msglen)
    # Handle all other message
    else:
        data = raw_msglen
        while raw_msglen:
            raw_msg = sock.recv(4096)
            data += raw_msg
            if len(raw_msg) < 4096:
                break
    # Return decoded text rather than bytes by default
    if isinstance(frmt, str):
        data = data.decode()
    return data


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


def client_sender(send_buffer, target, port, frmt=''):
    vprint('Connecting to {ip}'.format(ip=target))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        try:
            client.connect((target, port))

            if len(send_buffer) > 0:
                send_msg(client, send_buffer, frmt)
                vprint('Sent {buf}'.format(buf=send_buffer[:80]))
            while True:
                response = None
                start = time.time()
                while not response:
                    response = recv_msg(client)
                    if response:
                        print('{resp}'.format(
                            resp=response),
                            end='',
                            flush=True)
                        start = time.time()
                    else:
                        if time.time() - start > 10:
                            vprint('Timed out waiting for response.')
                            break
                # wait for more input
                send_buffer = input()
                send_buffer += '\n'

                if len(send_buffer):
                    send_msg(client, send_buffer, frmt)
        except Exception as ec:
            vprint('Problem connecting to {ip}\n{error}'.format(
                ip=target,
                error=ec))
            client.close()


def execute_command(command):
    if isinstance(command, bytes):
        command = command.decode()
    command = command.rstrip('\r\n')
    try:
        vprint('Executing command: {}'.format(command))
        output = subprocess.check_output(
            command,
            stderr=subprocess.STDOUT,
            shell=True,
            timeout=10)
    except Exception as ee:
        output = 'Failed to execute command. {error}\r\n'.format(error=ee)
    return output


def handle_client(client_socket, execute=None, upload=False, shell=False):
    vprint('Execute: {}'.format(execute))
    vprint('Upload: {}'.format(upload))
    vprint('Shell: {}'.format(shell))

    frmt = 'C7'

    if upload:
        file_buffer = b''
        file_buffer = recv_msg(client_socket, file_buffer)

        try:
            with open(upload, 'wb') as file_descriptor:
                file_descriptor.write(file_buffer)
                send_msg(
                    client_socket,
                    'Successfully saved file to {path}'.format(path=upload))
        except Exception as ehu:
            send_msg(
                client_socket,
                'Failed to save file to {path}'.format(path=upload))

    elif execute:
        output = execute_command(execute)
        send_msg(client_socket, output, frmt)

    elif shell:
        while True:
            # Show a simple command prompt
            send_msg(client_socket, '<PYC:#>', frmt)

            # Receive until linefeed
            cmd_buffer = ''
            while '\n' not in cmd_buffer:
                msg_resp = recv_msg(client_socket)
                if msg_resp:
                    cmd_buffer += msg_resp
                else:
                    cmd_buffer += '\n'

            # Send back the command output
            response = execute_command(cmd_buffer)
            send_msg(client_socket, response, frmt)

    else:
        # Print out what client sends
        request = recv_msg(client_socket)
        print('[*] Received: {req}'.format(req=request))

        # Send back a packet
        send_msg(client_socket, 'ACK!', frmt)
        client_socket.close()


def server_mode(bind_ip, bind_port, execute, upload, shell):
    # Run in server mode by default
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((str(bind_ip), int(bind_port)))
        server.listen(5)

        vprint('Listening on {ip}:{port}'.format(
            ip=bind_ip,
            port=bind_port))

        while True:
            try:
                client, addr = server.accept()
                vprint('Accepted connection from: {ip}:{port}'.format(
                    ip=addr[0],
                    port=addr[1]))

                # Spin up our client thread to handle incoming data
                client_handler = threading.Thread(
                    target=handle_client,
                    args=(client, execute, upload, shell))
                client_handler.start()
            except KeyboardInterrupt as ki:
                client_handler.end()
                server.close()
            except Exception as es:
                vprint('Server error. \n{error}'.format(error=es))
            # finally:
                break
    exit()


if __name__ == "__main__":
    listen = False
    shell = False
    upload = False
    execute = ''
    target = ''
    port = 0
    # Parse provided arguments
    a_parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            '''
Ncat replacement.
Examples:
1) nc_bhp.py -t target_host -p port
2) nc_bhp.py -t target_address -p port [-s shell]
3) nc_bhp.py [-l listen_address] [-p port] [-u upload_file_path]
4) nc_bhp.py [-l listen_address] [-p port] [-e command_to_execute]
            '''))
    mode = a_parser.add_mutually_exclusive_group()
    mode.add_argument(
        '-l',
        '--listen_addr',
        action='store_const',
        const='0.0.0.0',
        help='Address used to listen; [0.0.0.0]')
    mode.add_argument(
        '-t',
        '--target_host',
        help='Target address or hostname')
    a_parser.add_argument(
        '-p',
        '--port',
        type=int,
        default=7890,
        help='Listen on port or Port on which the target host listens; [7890]')
    a_parser.add_argument(
        '-s',
        '--shell',
        action='store_true',
        help='Sends an interactive shell over the connection.')
    a_parser.add_argument(
        '-e',
        '--execute',
        help='Command to execute: ["/usr/bin/bash"]')
    a_parser.add_argument(
        '-u',
        '--upload',
        help='Uploads a file using the destination path given.')
    a_parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Prints more messages about status.')
    a_parser.add_argument(
        '-7',
        '--c7',
        action='store_const',
        const='C7',
        help='Instructs client to use C7 formatted messages.')
    nc_bhp_args = a_parser.parse_args()

    # Go through each argument from the command line input
    if nc_bhp_args.verbose:
        verbose = nc_bhp_args.verbose

    if nc_bhp_args.c7:
        frmt = nc_bhp_args.c7
    else:
        frmt = ''

    if nc_bhp_args.shell:
        shell = nc_bhp_args.shell

    if nc_bhp_args.listen_addr:
        listen_addr = validate_ip(nc_bhp_args.listen_addr)
        vprint('Listening {ip}'.format(ip=listen_addr))
        listen = True

    if nc_bhp_args.target_host:
        target_addr = nc_bhp_args.target_host
        vprint('Target host {ip}'.format(ip=target_addr))
        target = nc_bhp_args.target_host

    if nc_bhp_args.port:
        port = int(nc_bhp_args.port)
        vprint('Using port {port}'.format(port=port))

    if nc_bhp_args.execute:
        execute = nc_bhp_args.execute

    if nc_bhp_args.upload:
        upload = Path(nc_bhp_args.upload)
        if upload.exists() is False or upload.is_dir() is True:
            vprint('Upload path is not valid.')
            upload = None

    # If connecting to target host
    if len(target) and port > 0:
        # Read in buffer
        client_sender(stdin.read(), target, port, frmt)
    elif listen:
        server_mode(listen_addr, port, execute, upload, shell)
    else:
        server_mode('0.0.0.0', 7890, False, '', True)
