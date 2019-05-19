import socket
import paramiko
import threading
import sys

host_key = paramiko.Ed25519Key(filename='ed25519Keyfilename')
verbose = False


def vprint(verbose_string, lverbose=False):
    global verbose
    if lverbose or verbose:
        if lverbose is True:
            icon = '*'
        else:
            icon = lverbose
        print('[{}] {}'.format(icon, verbose_string))


class Server (paramiko.ServerInterface):
    def _init_(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, passwd):
        if (username == 'bhp_user') and (passwd == 'Xn12az16'):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED


server = sys.argv[1]
ssh_port = int(sys.argv[2])

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((server, ssh_port))
        sock.listen(100)

        vprint('Listening for connection...', True)
        client, addr = sock.accept()
except Exception as em:
    vprint('Listen failed: {}'.format(em), '-')
    sys.exit(1)

vprint('Got a connection!')

try:
    sshSession = paramiko.Transport(client)
    sshSession.add_server_key(host_key)
    server = Server()
    try:
        sshSession.start_server(server=server)
    except paramiko.SSHException as essh:
        vprint('SSH negotiation failed.', '-')
    chan = sshSession.accept(20)
    vprint('Authenticated!' '+')
    print(chan.recv(1024))
    chan.send('Welcome to ssh_server')
    breakpoint()
    while True:
        try:
            command = input("Enter command: ").strip('\n')
            if command != 'exit':
                chan.send(command)
                print(chan.recv(1024).decode() + '\n')
            else:
                chan.send('exit')
                vprint('Exiting', True)
                sshSession.close()
                raise Exception('exit')
        except KeyboardInterrupt:
            sshSession.close()
except Exception as es:
    vprint('Caught Exception: {es}'.format(es=es))
    try:
        sshSession.close()
    except Exception:
        pass
finally:
    sys.exit(1)

