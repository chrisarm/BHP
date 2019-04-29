#!/usr/bin/env python3
from os import listdir


def run(**args):
    print('[*] In dir_list module.')
    files = listdir('.')
    return str(files)
