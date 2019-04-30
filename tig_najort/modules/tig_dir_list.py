#!/usr/bin/env python3
from os import listdir


def run(**args):
    print('[*] In dir_list module.')
    breakpoint()
    if args['test']==True:
        return 'Directory listing could be here'
    else:
        files = listdir('.')
        return str(files)
