#!/usr/bin/env python3
from os import listdir


def run(**args, test=False):
    print('[*] In dir_list module.')
    if test:
        return 'Directory listing could be here'
    else:
        files = listdir('.')
        return str(files)
