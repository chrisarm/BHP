#!/usr/bin/env python3
import ctypes
import msvcrt
import win32api
import random
import time
import sys
import vk_keys
import win32clipboard
import threading
import time 
from queue import SimpleQueue

print_lock = threading.Lock()
current_window = None
previous_time = time.gmtime()
key_queue = SimpleQueue()
vk = vk_keys.VK_Keys()

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

keystrokes = 0
mouse_clicks = 0
double_clicks = 0

verbose = True
test = True


class Last_Input_Info(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint),
                ("dwTime", ctypes.c_ulong)]


def vprint(verbose_string, lverbose=False):
    global verbose
    if lverbose or verbose:
        if lverbose:
            icon = lverbose
        else:
            icon = '*'
        print('[{}] {}'.format(icon, verbose_string), flush=True)


def get_last_input():
    global time_reported

    struct_last_input_info = Last_Input_Info()
    struct_last_input_info.cbSize = ctypes.sizeof(Last_Input_Info)

    # Get last registered input
    user32.GetLastInputInfo(ctypes.byref(struct_last_input_info))

    # Determine how long the machine has been running
    run_time = kernel32.GetTickCount()
    elapsed = run_time - struct_last_input_info.dwTime

    return elapsed


def check_key_press(last_key=None, key_list=vk.id_to_vk):
    '''
    -Returns the virtual key value if "listed"
    -Otherwise returns the string representation of the
    key that was pressed
    '''
    global mouse_clicks
    global keystrokes

    # if msvcrt.kbhit():
    #     key = msvcrt.getch()
    #     ord_key = ord(key)

    #     if ord_key != last_key:
    #         if ord_key in key_list:
    #             keystrokes += 1
    #         print('OrdKey: {}, LastKey: {}'.format(ord_key, last_key))
    #         return ord_key

    for key in key_list:
        key = int(key)
        key_state = win32api.GetAsyncKeyState(key)
        if key_state != 0:
            if key_state < 0 and key == 0x01 and key != last_key:
                mouse_clicks += 1
                return 0x01
            elif key_state < 0 and key != last_key:
                keystrokes += 1
                return key
            elif key_state < 0 and key == last_key:
                return key
            return None

    # for i in key_list:
    #     key_state = win32api.GetKeyState(i)

    #     if key_state != 0:
    #         # 0x1 => left-click
    #         if i == 0x01:
    #             mouse_clicks += 1
    #             return time.time()
    #         # Number Keys
    #         else:
    #             vprint(chr(i))
    #             keystrokes += 1
    #     elif key_state == 0:
    #         raise RuntimeWarning('Windows Key State Not Recognized')
    #     return None


def main(**args):
    # Only looking for printable or interesting key presses
    key_list = [0x01] + list(range(32, 127)) + list(vk.id_to_vk.keys())
    if test:
        # Build starting foundation for tracking key strokes.
        idle_sec = 0
        last_key = None
        last_key_time = kernel32.GetTickCount()
        new_key = None
        print_star = False
        while idle_sec < 2:  # Run until input stops for a few seconds
            try:
                idle = get_last_input()
                idle_sec = idle / 1000

                new_key = check_key_press(last_key=last_key, key_list=key_list)
                if new_key == last_key and last_key is not None:
                    if print_star and idle > 70:
                        print('*', end='', flush=True)
                        print_star = False
                    
                    if idle > 70:
                        last_key = None
                    
                    time.sleep(.07)  # Sleep to allow delay
                else:
                    if new_key is not None:
                        last_key = new_key

                        # Uncomment to see key press print out.
                        # if new_key >= 32 and new_key < 127:
                        #     key = chr(new_key)
                        # else:
                        #     key = vk.get_vk(new_key)
                        # print('{}'.format(key), end='', flush=True)

                        # Uncomment to print * for repeated key
                        # print_star = True

            except RuntimeWarning as rwe:
                pass
        vprint('\n------------\n')
        vprint('Done Testing for sandbox.')
        vprint('Mouse clicks: {}'.format(mouse_clicks))
        vprint('Keystrokes: {}'.format(keystrokes))


if __name__ == '__main__':
    main(test=test)
