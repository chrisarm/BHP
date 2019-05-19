#!/usr/bin/env python3
'''
Use for finding privileged process as they are created
'''

import win32con
import win32api
import win32security

import wmi
import time


def log_to_file(message):
    with open('process_monitor_log.csv', "ab") as fd:
        message = '{}\r\n'.format(message).encode()
        fd.write(message)
        time.sleep(.01)
    return


def get_process_privileges(pid):
    priv_list = list()
    try:
        # Obtain a handle to the target process
        hproc = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION,
            False,
            pid)

        # Open the main process token
        htok = win32security.OpenProcessToken(hproc, win32con.TOKEN_QUERY)

        # Retrieve the list of privileges enabled
        privs = win32security.GetTokenInformation(
            htok,
            win32security.TokenPrivileges)

        # Iterate over the privs and output the ones that are enabled
        for priv in privs:
            if priv[1] == 3:
                # Formatting for multiple privs
                if len(priv_list) >= 1:
                    priv_list[-1] = priv_list[-1] + '|'

                # Append newly found priv
                priv_list.append('{}'.format(win32security.LookupPrivilegeName(
                    None, priv[0])))
    except Exception as e0:
        raise

    if priv_list and len(priv_list) >= 1:
        return priv_list
    else:
        return 'N/A'


# Instantiate the WMI interface
c = wmi.WMI()

# Create our process monitor
process_monitor = c.Win32_Process.watch_for('creation')

# Create CSV file column headers
log_to_file('Time,User,Executable,CommandLine,PID,Parent PID, Privileges')

while True:
    try:
        new_process = process_monitor()
        create_date = new_process.CreationDate
        proc_owner = new_process.GetOwner()
        proc_owner = '{},{}'.format(proc_owner[0], proc_owner[2])
        executable = new_process.ExecutablePath
        cmdline = new_process.CommandLine
        pid = new_process.ProcessId
        parent_pid = new_process.ParentProcessId

        privileges = get_process_privileges(pid)

        process_log_list = [
            create_date,
            proc_owner,
            executable,
            cmdline,
            str(pid),
            str(parent_pid),
            privileges,
            '\r\n']

        proc_log_message = ','.join([str(item) for item in process_log_list])

        print(proc_log_message, flush=True)
        log_to_file(proc_log_message)
    except KeyboardInterrupt as k1:
        raise
    except Exception as e1:
        print('Problem with process {} Owned by {}:\n{}'.format(
            pid,
            proc_owner,
            e1))
        pass
