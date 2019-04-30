#!/usr/bin/env python3
import os


def run(**args):
    print('[*] In environment module')
    if 'test' in args:
        return 'Environment variables could be printed'
    else:
        return str(os.environ)
