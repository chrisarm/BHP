import win32gui
import win32ui
import win32con
import win32api
from pathlib import Path
from os import listdir


def get_pad(number, step=10):
    '''
    Does the math for generating '0' padded file name numbers
    '''
    pad = '0'
    if isinstance(step, int) and step != 0:
        while (number / step) > step:
            number = number / step
            pad = pad + '0'
    else:
        raise ValueError('step not valid')


def run(**args):
    # Grab a handle to the main desktop window
    hdesktop = win32gui.GetDesktopWindow()

    # Determine the size of all monitors in pixels
    width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
    top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)

    # Create a device context
    desktop_dc = win32gui.GetWindowDC(hdesktop)
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)

    # Create a memory based device context
    mem_dc = img_dc.CreateCompatibleDC()

    # Create a bitmap object
    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(img_dc, width, height)
    mem_dc.SelectObject(screenshot)

    # Get ready to save the screenshot
    base = 'C:\\temp'
    files = None

    # Get a list of files in the curent directory to make sure this
    # doesn't overwrite anything
    try:
        files = listdir(base)
    except FileNotFoundError as fnf:
        Path.mkdir(Path(base))
        pass

    # Create unique filename with 0-padded number ID on the end
    number = 0
    pad = '0'
    step = 10
    while ('image{pad}{num}.bmp'.format(pad=pad, num=number) in files):
        plus10 = number + step
        if 'image{pad}{num}.bmp'.format(pad=pad, num=plus10) in files:
            number = plus10
            pad = get_pad(number, step)
        else:
            number += 1

    filename = '{base}\\image{pad}{num}.bmp'.format(
        base=base,
        pad=pad,
        num=number)

    # Copy the screen into our memory device context
    mem_dc.BitBlt(
        (0, 0),
        (width, height),
        img_dc,
        (left, top),
        win32con.SRCCOPY)
    screenshot.SaveBitmapFile(mem_dc, filename)

    # Free our objects
    mem_dc.DeleteDC()
    win32gui.DeleteObject(screenshot.GetHandle())


if __name__ == '__main__':
    run()
