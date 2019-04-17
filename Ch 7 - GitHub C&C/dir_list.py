#!/usr/bin/env python3
import os


def run(**args):
    print('[*] In dir_list module.')
    files = os.listdir('.')
    return str(files)
